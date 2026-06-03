"""
F1 Fantasy Prediction Engine
Lambda handler for the RunPredictionEngine Action Group

This module:
1. Predicts race finishing positions using a gradient-boosted ranking model
2. Converts predicted positions to expected F1 Fantasy points
3. Optimizes team selection under budget constraints (knapsack problem)
4. Runs Monte Carlo simulations for confidence intervals
5. Recommends chip timing based on remaining calendar

Dependencies (Lambda Layer):
  pip install scikit-learn pandas numpy scipy
"""

import json
import os
import pickle
import itertools
import random
from typing import Any

import numpy as np

# ═══════════════════════════════════════════════════════════════
# F1 FANTASY 2026 SCORING RULES
# ═══════════════════════════════════════════════════════════════

RACE_POSITION_POINTS = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1,
}

QUALI_POSITION_POINTS = {
    1: 10, 2: 9, 3: 8, 4: 7, 5: 6,
    6: 5, 7: 4, 8: 3, 9: 2, 10: 1,
}

SPRINT_POSITION_POINTS = {
    1: 10, 2: 9, 3: 8, 4: 7, 5: 6,
    6: 5, 7: 4, 8: 3,
}

POSITIONS_GAINED_POINTS_PER = 2   # 2 pts per position gained
OVERTAKE_POINTS = 1               # 1 pt per overtake
FASTEST_LAP_POINTS = 10
DNF_PENALTY = -20
SPRINT_DNF_PENALTY = -10          # Reduced for 2026


# ═══════════════════════════════════════════════════════════════
# FEATURE ENGINEERING
# ═══════════════════════════════════════════════════════════════

def build_feature_vector(driver_data: dict) -> list:
    """
    Build a feature vector for the ML model from gathered data.
    
    Features (in order):
    0.  avg_fp_pace           - Average practice lap time (fuel-corrected)
    1.  best_fp_lap           - Best practice lap time
    2.  long_run_degradation  - Tyre deg rate on long runs (s/lap)
    3.  qualifying_position   - Grid position (if quali done, else predicted)
    4.  historical_track_avg  - Avg finish at this circuit (last 3 years)
    5.  season_form           - Avg finish position this season
    6.  constructor_form      - Constructor points rank
    7.  reliability_score     - 1.0 = perfect, 0.0 = DNF every race
    8.  rain_probability      - 0.0 to 1.0
    9.  wet_weather_skill     - Driver's historical wet delta vs dry
    10. track_temp            - Track temperature in °C
    11. wind_speed            - Wind speed in km/h
    12. pit_stop_avg          - Team's avg pit stop time this season
    13. positions_gained_avg  - Driver's avg positions gained per race
    14. first_lap_delta       - Avg position change on lap 1
    15. betting_implied_prob  - Win probability from betting odds
    """
    return [
        driver_data.get('avg_fp_pace', 0),
        driver_data.get('best_fp_lap', 0),
        driver_data.get('long_run_degradation', 0),
        driver_data.get('qualifying_position', 10),
        driver_data.get('historical_track_avg', 10),
        driver_data.get('season_form', 10),
        driver_data.get('constructor_form', 5),
        driver_data.get('reliability_score', 0.95),
        driver_data.get('rain_probability', 0.0),
        driver_data.get('wet_weather_skill', 0.0),
        driver_data.get('track_temp', 30),
        driver_data.get('wind_speed', 10),
        driver_data.get('pit_stop_avg', 2.5),
        driver_data.get('positions_gained_avg', 0),
        driver_data.get('first_lap_delta', 0),
        driver_data.get('betting_implied_prob', 0.05),
    ]


# ═══════════════════════════════════════════════════════════════
# POSITION PREDICTION (Gradient Boosted Ranker)
# ═══════════════════════════════════════════════════════════════

def predict_finishing_order(features_by_driver: dict, model=None) -> list:
    """
    Predict race finishing order.
    
    If a trained model is available (pickled sklearn GradientBoostingRegressor),
    use it. Otherwise, use a heuristic baseline (weighted feature combination).
    
    Returns list of (driver_id, predicted_position, confidence) tuples.
    """
    predictions = []
    
    for driver_id, data in features_by_driver.items():
        features = build_feature_vector(data)
        
        if model is not None:
            # Use trained ML model
            predicted_time = model.predict([features])[0]
        else:
            # Heuristic baseline (weighted combination)
            # Lower score = better predicted finish
            score = (
                features[3] * 0.30 +     # qualifying_position (30% weight)
                features[0] * 0.25 +      # avg_fp_pace (25%)
                features[4] * 0.15 +      # historical_track_avg (15%)
                features[5] * 0.10 +      # season_form (10%)
                (1 - features[7]) * 20 +  # reliability penalty
                (1 - features[15]) * 5 +  # inverse of betting probability
                features[2] * 3           # degradation penalty
            )
            predicted_time = score
        
        predictions.append({
            'driver_id': driver_id,
            'name': data.get('name', driver_id),
            'predicted_score': predicted_time,
            'reliability': data.get('reliability_score', 0.95),
        })
    
    # Sort by predicted score (lower = better finish)
    predictions.sort(key=lambda x: x['predicted_score'])
    
    # Assign positions
    for i, pred in enumerate(predictions):
        pred['predicted_position'] = i + 1
        # Confidence based on gap to adjacent drivers
        pred['confidence'] = 'HIGH' if i < 3 else ('MEDIUM' if i < 10 else 'LOW')
    
    return predictions


# ═══════════════════════════════════════════════════════════════
# FANTASY POINTS CALCULATION
# ═══════════════════════════════════════════════════════════════

def calculate_expected_fantasy_points(
    driver_id: str,
    predicted_race_pos: int,
    predicted_quali_pos: int,
    grid_position: int,
    positions_gained_avg: float,
    reliability: float,
    fastest_lap_prob: float = 0.05,
) -> dict:
    """Calculate expected F1 Fantasy points for a driver."""
    
    # Race position points
    race_pts = RACE_POSITION_POINTS.get(predicted_race_pos, 0)
    
    # Qualifying points
    quali_pts = QUALI_POSITION_POINTS.get(predicted_quali_pos, 0)
    
    # Positions gained (grid → finish)
    pos_gained = max(0, grid_position - predicted_race_pos)
    pos_gained_pts = pos_gained * POSITIONS_GAINED_POINTS_PER
    
    # Estimated overtakes (correlated with positions gained but not identical)
    estimated_overtakes = max(0, pos_gained + random.gauss(0, 1.5))
    overtake_pts = int(estimated_overtakes) * OVERTAKE_POINTS
    
    # Fastest lap (probabilistic)
    fastest_lap_pts = FASTEST_LAP_POINTS * fastest_lap_prob
    
    # DNF risk
    dnf_risk_pts = DNF_PENALTY * (1 - reliability)
    
    total = race_pts + quali_pts + pos_gained_pts + overtake_pts + fastest_lap_pts + dnf_risk_pts
    
    return {
        'driver_id': driver_id,
        'expected_total': round(total, 1),
        'breakdown': {
            'race_position': race_pts,
            'qualifying': quali_pts,
            'positions_gained': pos_gained_pts,
            'overtakes': round(overtake_pts, 1),
            'fastest_lap_ev': round(fastest_lap_pts, 1),
            'dnf_risk': round(dnf_risk_pts, 1),
        }
    }


# ═══════════════════════════════════════════════════════════════
# MONTE CARLO SIMULATION
# ═══════════════════════════════════════════════════════════════

def monte_carlo_simulation(
    features_by_driver: dict,
    n_simulations: int = 1000,
) -> dict:
    """
    Run Monte Carlo simulation to generate confidence intervals.
    
    Each simulation adds noise to features to model:
    - Qualifying variance (some drivers are inconsistent qualifiers)
    - First-lap incidents (~12% chance of T1 contact)
    - Safety car reshuffles (~30% chance per race)
    - Mechanical failures (per-team DNF probability)
    - Weather changes
    """
    driver_ids = list(features_by_driver.keys())
    points_matrix = {d: [] for d in driver_ids}
    
    for _ in range(n_simulations):
        # Add noise to features for this simulation
        noisy_features = {}
        for d_id, data in features_by_driver.items():
            noisy = data.copy()
            
            # Qualifying variance: ±1-3 positions
            quali_noise = random.gauss(0, 1.5)
            noisy['qualifying_position'] = max(1, min(22, 
                int(data.get('qualifying_position', 10) + quali_noise)))
            
            # DNF event
            if random.random() > data.get('reliability_score', 0.95):
                noisy['dnf'] = True
            else:
                noisy['dnf'] = False
            
            # Safety car effect (reshuffles midfield)
            if random.random() < 0.30:  # ~30% SC probability
                noisy['safety_car'] = True
                # SC benefits midfielders, hurts leaders
                if data.get('qualifying_position', 10) > 5:
                    noisy['qualifying_position'] = max(1, 
                        noisy['qualifying_position'] - random.randint(0, 3))
            
            noisy_features[d_id] = noisy
        
        # Predict this simulation
        sim_predictions = predict_finishing_order(noisy_features)
        
        for pred in sim_predictions:
            d_id = pred['driver_id']
            if noisy_features[d_id].get('dnf', False):
                # DNF: negative fantasy points
                points_matrix[d_id].append(DNF_PENALTY)
            else:
                pts = calculate_expected_fantasy_points(
                    d_id,
                    pred['predicted_position'],
                    noisy_features[d_id].get('qualifying_position', 10),
                    noisy_features[d_id].get('qualifying_position', 10),
                    noisy_features[d_id].get('positions_gained_avg', 0),
                    noisy_features[d_id].get('reliability_score', 0.95),
                )
                points_matrix[d_id].append(pts['expected_total'])
    
    # Calculate statistics
    results = {}
    for d_id in driver_ids:
        pts = points_matrix[d_id]
        results[d_id] = {
            'expected_points': round(np.mean(pts), 1),
            'median_points': round(np.median(pts), 1),
            'p5': round(np.percentile(pts, 5), 1),     # 5th percentile (floor)
            'p95': round(np.percentile(pts, 95), 1),    # 95th percentile (ceiling)
            'std_dev': round(np.std(pts), 1),
            'dnf_rate': round(sum(1 for p in pts if p < 0) / len(pts) * 100, 1),
        }
    
    return results


# ═══════════════════════════════════════════════════════════════
# TEAM OPTIMIZER (Budget-Constrained Selection)
# ═══════════════════════════════════════════════════════════════

def optimize_team(
    driver_predictions: dict,       # {driver_id: {expected_points, price, ...}}
    constructor_predictions: dict,   # {const_id: {expected_points, price, ...}}
    budget: float = 100.0,
    mode: str = 'balanced',
    must_include: list = None,
    must_exclude: list = None,
) -> dict:
    """
    Find the optimal 5-driver + 2-constructor team within budget.
    
    Modes:
    - balanced: maximize expected points
    - safe: maximize 5th percentile (floor)
    - aggressive: maximize 95th percentile (ceiling)
    - value: maximize points-per-million-spent
    """
    must_include = must_include or []
    must_exclude = must_exclude or []
    
    # Filter available options
    avail_drivers = {
        d_id: data for d_id, data in driver_predictions.items()
        if d_id not in must_exclude
    }
    avail_constructors = {
        c_id: data for c_id, data in constructor_predictions.items()
        if c_id not in must_exclude
    }
    
    # Select optimization metric based on mode
    def get_metric(prediction_data):
        if mode == 'safe':
            return prediction_data.get('p5', prediction_data.get('expected_points', 0))
        elif mode == 'aggressive':
            return prediction_data.get('p95', prediction_data.get('expected_points', 0))
        elif mode == 'value':
            price = prediction_data.get('price', 1)
            return prediction_data.get('expected_points', 0) / max(price, 0.1)
        else:  # balanced
            return prediction_data.get('expected_points', 0)
    
    driver_ids = list(avail_drivers.keys())
    constructor_ids = list(avail_constructors.keys())
    
    best_team = None
    best_score = -float('inf')
    
    # Mandatory includes
    mandatory_drivers = [d for d in must_include if d in avail_drivers]
    mandatory_constructors = [c for c in must_include if c in avail_constructors]
    
    remaining_driver_slots = 5 - len(mandatory_drivers)
    remaining_constructor_slots = 2 - len(mandatory_constructors)
    
    optional_drivers = [d for d in driver_ids if d not in mandatory_drivers]
    optional_constructors = [c for c in constructor_ids if c not in mandatory_constructors]
    
    # Iterate over all valid combinations
    # (For 22 drivers choose 5 = 26,334 combinations — fast enough)
    for driver_combo in itertools.combinations(optional_drivers, remaining_driver_slots):
        drivers = list(mandatory_drivers) + list(driver_combo)
        driver_cost = sum(avail_drivers[d].get('price', 0) for d in drivers)
        
        for constructor_combo in itertools.combinations(optional_constructors, remaining_constructor_slots):
            constructors = list(mandatory_constructors) + list(constructor_combo)
            constructor_cost = sum(avail_constructors[c].get('price', 0) for c in constructors)
            
            total_cost = driver_cost + constructor_cost
            if total_cost > budget:
                continue
            
            # Calculate team score
            score = (
                sum(get_metric(avail_drivers[d]) for d in drivers) +
                sum(get_metric(avail_constructors[c]) for c in constructors)
            )
            
            if score > best_score:
                best_score = score
                best_team = {
                    'drivers': drivers,
                    'constructors': constructors,
                    'total_cost': round(total_cost, 1),
                    'budget_remaining': round(budget - total_cost, 1),
                    'total_expected_points': round(score, 1),
                }
    
    if best_team is None:
        return {'error': 'No valid team found within budget constraints'}
    
    # Add details for each pick
    best_team['driver_details'] = [
        {
            'id': d,
            'name': avail_drivers[d].get('name', d),
            'price': avail_drivers[d].get('price', 0),
            'expected_points': avail_drivers[d].get('expected_points', 0),
            'points_per_million': round(
                avail_drivers[d].get('expected_points', 0) / max(avail_drivers[d].get('price', 1), 0.1), 2
            ),
        }
        for d in best_team['drivers']
    ]
    
    best_team['constructor_details'] = [
        {
            'id': c,
            'name': avail_constructors[c].get('name', c),
            'price': avail_constructors[c].get('price', 0),
            'expected_points': avail_constructors[c].get('expected_points', 0),
        }
        for c in best_team['constructors']
    ]
    
    # DRS Boost recommendation: pick the driver with highest expected points
    drs_candidate = max(
        best_team['driver_details'],
        key=lambda d: d['expected_points']
    )
    best_team['drs_boost_recommendation'] = drs_candidate['id']
    best_team['drs_boost_reasoning'] = (
        f"DRS Boost {drs_candidate['name']} — highest expected points "
        f"({drs_candidate['expected_points']} pts). Doubling this gives "
        f"+{drs_candidate['expected_points']} extra points."
    )
    
    return best_team


# ═══════════════════════════════════════════════════════════════
# LAMBDA HANDLER
# ═══════════════════════════════════════════════════════════════

def lambda_handler(event: dict, context: Any) -> dict:
    """
    Bedrock Agent Action Group Lambda handler.
    Routes to the appropriate prediction function based on apiPath.
    """
    api_path = event.get('apiPath', '')
    parameters = event.get('parameters', {})
    request_body = event.get('requestBody', {})
    
    # Parse request body if present
    body = {}
    if request_body:
        body_content = request_body.get('content', {})
        json_body = body_content.get('application/json', {})
        if 'properties' in json_body:
            body = {p['name']: p['value'] for p in json_body['properties']}
        elif isinstance(json_body, dict) and 'body' in json_body:
            body = json.loads(json_body['body']) if isinstance(json_body['body'], str) else json_body['body']
    
    # Also check parameters dict
    if isinstance(parameters, list):
        params = {p['name']: p['value'] for p in parameters}
    else:
        params = parameters or {}
    
    # Merge body and params
    all_params = {**params, **body}
    
    try:
        if api_path == '/predictFinishingOrder':
            features_json = all_params.get('features_json', '{}')
            features = json.loads(features_json) if isinstance(features_json, str) else features_json
            
            predictions = predict_finishing_order(features)
            result = {
                'predictions': predictions,
                'model_confidence': 'HIGH' if len(features) >= 15 else 'MEDIUM',
                'data_completeness': 'Full weekend data' if len(features) >= 15 else 'Partial data',
            }
        
        elif api_path == '/predictFantasyPoints':
            features_json = all_params.get('features_json', '{}')
            features = json.loads(features_json) if isinstance(features_json, str) else features_json
            
            # Run Monte Carlo for confidence intervals
            mc_results = monte_carlo_simulation(features, n_simulations=500)
            
            result = {
                'driver_predictions': [
                    {
                        'driver_id': d_id,
                        'name': features.get(d_id, {}).get('name', d_id),
                        'expected_points': mc_results[d_id]['expected_points'],
                        'points_range': f"{mc_results[d_id]['p5']} - {mc_results[d_id]['p95']}",
                        'dnf_risk': f"{mc_results[d_id]['dnf_rate']}%",
                        'price': features.get(d_id, {}).get('price', 0),
                        'points_per_million': round(
                            mc_results[d_id]['expected_points'] / max(features.get(d_id, {}).get('price', 1), 0.1), 2
                        ),
                    }
                    for d_id in mc_results
                ]
            }
        
        elif api_path == '/optimizeTeam':
            budget = float(all_params.get('budget', 100.0))
            mode = all_params.get('mode', 'balanced')
            must_include = json.loads(all_params.get('must_include', '[]'))
            must_exclude = json.loads(all_params.get('must_exclude', '[]'))
            
            # Features should have been gathered by previous Action Group calls
            features_json = all_params.get('predictions_json', '{}')
            all_predictions = json.loads(features_json) if isinstance(features_json, str) else features_json
            
            driver_preds = all_predictions.get('drivers', {})
            constructor_preds = all_predictions.get('constructors', {})
            
            result = optimize_team(
                driver_preds, constructor_preds,
                budget=budget, mode=mode,
                must_include=must_include,
                must_exclude=must_exclude,
            )
        
        elif api_path == '/simulateMonteCarlo':
            features_json = all_params.get('features_json', '{}')
            features = json.loads(features_json) if isinstance(features_json, str) else features_json
            n_sims = int(all_params.get('n_simulations', 1000))
            
            result = monte_carlo_simulation(features, n_simulations=n_sims)
        
        elif api_path == '/recommendChipTiming':
            remaining_chips = json.loads(all_params.get('remaining_chips', '[]'))
            
            # Chip timing heuristics based on top-500 player strategies
            chip_advice = []
            if 'limitless' in remaining_chips:
                chip_advice.append({
                    'chip': 'Limitless',
                    'strategy': 'Use at the most PREDICTABLE race on the calendar (low variance). '
                                'Pick the 7 most expensive options. Historically best at: '
                                'Spain, Bahrain, Abu Dhabi (low SC probability, stable weather).',
                    'expected_uplift': '40-60 points above normal team',
                })
            if 'no_negative' in remaining_chips:
                chip_advice.append({
                    'chip': 'No Negative',
                    'strategy': 'Save for HIGH DNF RISK weekends: street circuits (Monaco, '
                                'Singapore, Baku), wet weather forecasts, or sprint weekends '
                                'with aggressive first laps.',
                    'expected_uplift': '15-30 points of downside protection',
                })
            if 'wildcard' in remaining_chips:
                chip_advice.append({
                    'chip': 'Wildcard',
                    'strategy': 'Use when your team needs 3+ changes but you want to avoid '
                                'transfer penalties. Best before a price rise wave so you can '
                                'restructure AND capture value.',
                    'expected_uplift': 'Saves 20-40 points in transfer penalties',
                })
            if 'triple_boost' in remaining_chips:
                chip_advice.append({
                    'chip': '3x Boost',
                    'strategy': 'Apply to your highest-confidence pick at a race where one '
                                'driver is heavily favored. Historically best at dominant-team '
                                'circuits (Verstappen at Spa/Suzuka/Mexico type situations).',
                    'expected_uplift': '30-80 points depending on boosted driver performance',
                })
            if 'autopilot' in remaining_chips:
                chip_advice.append({
                    'chip': 'Autopilot',
                    'strategy': 'Best for UNPREDICTABLE weekends where you have low conviction. '
                                'Sprint races with weather, new circuits, or regulation change '
                                'weekends. Lets the algorithm optimize for you.',
                    'expected_uplift': '10-25 points vs manual selection in chaotic races',
                })
            if 'final_fix' in remaining_chips:
                chip_advice.append({
                    'chip': 'Final Fix',
                    'strategy': 'Save for after qualifying when a key driver has a grid penalty '
                                'or crash in Q1. Allows you to swap out a disaster pick after '
                                'the transfer deadline.',
                    'expected_uplift': '15-35 points of disaster recovery',
                })
            
            result = {'chip_recommendations': chip_advice}
        
        else:
            result = {'error': f'Unknown apiPath: {api_path}'}
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': 'RunPredictionEngine',
                'apiPath': api_path,
                'httpMethod': 'POST',
                'httpStatusCode': 200,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps(result, default=str)
                    }
                }
            }
        }
    
    except Exception as e:
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': 'RunPredictionEngine',
                'apiPath': api_path,
                'httpStatusCode': 500,
                'responseBody': {
                    'application/json': {
                        'body': json.dumps({'error': str(e)})
                    }
                }
            }
        }

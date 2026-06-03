import '@copilotkit/react-ui/styles.css'
import { CopilotChat } from '@copilotkit/react-ui'
import { useCoAgentStateRender } from '@copilotkit/react-core'
import { TeamRecommendationCard } from './TeamRecommendationCard'

interface Props {
  sessionId: string
}

export function AdvisorChat({ sessionId: _sessionId }: Props) {
  // Render TeamRecommendationCard when the agent calls display_team_recommendation
  useCoAgentStateRender({
    name: 'display_team_recommendation',
    render: ({ state, status }) => (
      <TeamRecommendationCard recommendation={state} status={status} />
    ),
  })

  return (
    <div className="flex flex-col h-full">
      <CopilotChat
        className="flex-1"
        labels={{
          title: 'F1 Fantasy Advisor',
          initial: "Hi! I'm your F1 Fantasy Advisor. Ask me for a team recommendation for the upcoming race.",
          placeholder: 'Ask for a team recommendation…',
        }}
      />
    </div>
  )
}

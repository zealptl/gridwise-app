import { useParams } from 'react-router-dom'

export default function TeamDetail() {
  const { id } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Team Details</h1>
      <p>Team ID: {id}</p>
    </div>
  )
}

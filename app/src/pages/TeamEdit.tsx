import { useParams } from 'react-router-dom'

export default function TeamEdit() {
  const { id } = useParams()

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Edit Team</h1>
      <p>Team ID: {id}</p>
    </div>
  )
}

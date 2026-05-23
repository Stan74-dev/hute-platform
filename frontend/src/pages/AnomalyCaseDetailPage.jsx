import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import API from '../api/client'

const BACKEND_BASE_URL = 'http://127.0.0.1:8000'

export default function AnomalyCaseDetailPage() {
  const { caseId } = useParams()
  const navigate = useNavigate()
  const fileInputRef = useRef(null)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploadingEvidence, setUploadingEvidence] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const [caseData, setCaseData] = useState(null)
  const [assignableUsers, setAssignableUsers] = useState([])

  const [editStatus, setEditStatus] = useState('open')
  const [editPriority, setEditPriority] = useState('medium')
  const [editAssignedTo, setEditAssignedTo] = useState('')
  const [editNotes, setEditNotes] = useState('')
  const [editResolutionNotes, setEditResolutionNotes] = useState('')
  const [evidenceNote, setEvidenceNote] = useState('')

  const loadAssignableUsers = async () => {
    const response = await API.get('/accounts/anomaly-cases/?page=1&page_size=1')
    setAssignableUsers(response.data.assignable_users || [])
  }

  const loadCaseDetail = async () => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')

      const [caseResponse] = await Promise.all([
        API.get(`/accounts/anomaly-cases/${caseId}/`),
        loadAssignableUsers(),
      ])

      const caseObj = caseResponse.data.case
      setCaseData(caseObj)
      setEditStatus(caseObj.status || 'open')
      setEditPriority(caseObj.priority || 'medium')
      setEditAssignedTo(caseObj.assigned_to_id || '')
      setEditNotes(caseObj.notes || '')
      setEditResolutionNotes(caseObj.resolution_notes || '')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not load anomaly case.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCaseDetail()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId])

  const saveCase = async () => {
    try {
      setSaving(true)
      setError('')
      setSuccess('')

      await API.patch(`/accounts/anomaly-cases/${caseId}/`, {
        status: editStatus,
        priority: editPriority,
        assigned_to_id: editAssignedTo || null,
        notes: editNotes,
        resolution_notes: editResolutionNotes,
      })

      setSuccess('Case updated.')
      await loadCaseDetail()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not update case.')
    } finally {
      setSaving(false)
    }
  }

  const uploadEvidence = async () => {
    const file = fileInputRef.current?.files?.[0]
    if (!file) {
      setError('Choose a file to upload.')
      return
    }

    try {
      setUploadingEvidence(true)
      setError('')
      setSuccess('')

      const formData = new FormData()
      formData.append('file', file)
      formData.append('note', evidenceNote)

      await API.post(`/accounts/anomaly-cases/${caseId}/evidence/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setSuccess('Evidence uploaded.')
      setEvidenceNote('')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }

      await loadCaseDetail()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not upload evidence.')
    } finally {
      setUploadingEvidence(false)
    }
  }

  const downloadEvidence = async (evidenceId, filename) => {
    try {
      setError('')
      setSuccess('')

      const response = await API.get(`/accounts/anomaly-evidence/${evidenceId}/download/`, {
        responseType: 'blob',
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', filename || `evidence_${evidenceId}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      setSuccess('Evidence downloaded.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not download evidence.')
    }
  }

  const exportPdf = () => {
    window.open(`${BACKEND_BASE_URL}/api/dashboard/export/case/${caseId}/`, '_blank')
  }

  if (loading) {
    return <p>Loading case detail...</p>
  }

  if (!caseData) {
    return <p>Case not found.</p>
  }

  return (
    <div>
      <div className="section-header">
        <h2>Case Detail</h2>
        <p className="muted-text">
          Full-screen investigation view for anomaly case #{caseData.id}.
        </p>
      </div>

      <div style={{ marginTop: '12px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
        <Link to="/anomaly-cases" className="btn btn-secondary">
          Back to Case Register
        </Link>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => navigate(-1)}
        >
          Go Back
        </button>
        <button
          type="button"
          className="btn btn-primary"
          onClick={exportPdf}
        >
          Export PDF
        </button>
      </div>

      {error ? <p className="error-text" style={{ marginTop: '16px' }}>{error}</p> : null}
      {success ? <p style={{ color: 'green', marginTop: '16px' }}>{success}</p> : null}

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Case Overview</h3>

          <div style={{ marginTop: '12px' }}>
            <p><strong>ID:</strong> {caseData.id}</p>
            <p><strong>Title:</strong> {caseData.title}</p>
            <p><strong>Description:</strong> {caseData.description}</p>
            <p><strong>Anomaly Type:</strong> {caseData.anomaly_type}</p>
            <p><strong>Severity:</strong> {caseData.severity}</p>
            <p><strong>Score:</strong> {caseData.score}</p>
            <p><strong>Status:</strong> {caseData.status}</p>
            <p><strong>Priority:</strong> {caseData.priority}</p>
            <p><strong>Assigned To:</strong> {caseData.assigned_to_username || '-'}</p>
            <p><strong>Created By:</strong> {caseData.created_by_username || '-'}</p>
            <p><strong>Auto Created:</strong> {caseData.auto_created ? 'Yes' : 'No'}</p>
            <p><strong>Detected Date:</strong> {caseData.detected_date || '-'}</p>
            <p><strong>SLA Due:</strong> {caseData.sla_due_at || '-'}</p>
            <p><strong>SLA Status:</strong> {caseData.sla_breached ? 'Breached' : 'Healthy'}</p>
            <p><strong>Escalation Level:</strong> {caseData.escalation_level || 0}</p>
            <p><strong>Escalated At:</strong> {caseData.escalated_at || '-'}</p>
            <p><strong>Created At:</strong> {caseData.created_at || '-'}</p>
            <p><strong>Updated At:</strong> {caseData.updated_at || '-'}</p>
            <p><strong>Closed At:</strong> {caseData.closed_at || '-'}</p>
          </div>
        </div>

        <div className="content-card">
          <h3>Manage Case</h3>

          <label style={{ marginTop: '12px', display: 'block' }}>Status</label>
          <select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
            <option value="open">Open</option>
            <option value="investigating">Investigating</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>

          <label style={{ marginTop: '12px', display: 'block' }}>Priority</label>
          <select value={editPriority} onChange={(e) => setEditPriority(e.target.value)}>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>

          <label style={{ marginTop: '12px', display: 'block' }}>Assign To</label>
          <select value={editAssignedTo} onChange={(e) => setEditAssignedTo(e.target.value)}>
            <option value="">Unassigned</option>
            {assignableUsers.map((u) => (
              <option key={u.id} value={u.id}>{u.username}</option>
            ))}
          </select>

          <label style={{ marginTop: '12px', display: 'block' }}>Notes</label>
          <textarea
            rows="6"
            value={editNotes}
            onChange={(e) => setEditNotes(e.target.value)}
          />

          <label style={{ marginTop: '12px', display: 'block' }}>Resolution Notes</label>
          <textarea
            rows="6"
            value={editResolutionNotes}
            onChange={(e) => setEditResolutionNotes(e.target.value)}
          />

          <button
            type="button"
            className="btn btn-primary"
            style={{ marginTop: '16px' }}
            onClick={saveCase}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Case'}
          </button>
        </div>
      </div>

      <div className="card-grid" style={{ marginTop: '20px' }}>
        <div className="content-card">
          <h3>Evidence Upload</h3>

          <div style={{ marginTop: '10px' }}>
            <input ref={fileInputRef} type="file" />
          </div>

          <div style={{ marginTop: '10px' }}>
            <textarea
              rows="4"
              placeholder="Evidence note"
              value={evidenceNote}
              onChange={(e) => setEvidenceNote(e.target.value)}
            />
          </div>

          <button
            type="button"
            className="btn btn-secondary"
            style={{ marginTop: '12px' }}
            onClick={uploadEvidence}
            disabled={uploadingEvidence}
          >
            {uploadingEvidence ? 'Uploading...' : 'Upload Evidence'}
          </button>

          <div style={{ marginTop: '20px' }}>
            <strong>Evidence Items</strong>

            {!caseData.evidence_items || caseData.evidence_items.length === 0 ? (
              <p style={{ marginTop: '8px' }}>No evidence uploaded yet.</p>
            ) : (
              <div className="table-wrap" style={{ marginTop: '10px' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Filename</th>
                      <th>Note</th>
                      <th>Uploaded By</th>
                      <th>Created At</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {caseData.evidence_items.map((ev) => (
                      <tr key={ev.id}>
                        <td>{ev.original_filename}</td>
                        <td>{ev.note || '-'}</td>
                        <td>{ev.uploaded_by_username || '-'}</td>
                        <td>{ev.created_at || '-'}</td>
                        <td>
                          <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => downloadEvidence(ev.id, ev.original_filename)}
                          >
                            Download
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <div className="content-card">
          <h3>Activity Timeline</h3>

          {!caseData.timeline || caseData.timeline.length === 0 ? (
            <p style={{ marginTop: '8px' }}>No activity yet.</p>
          ) : (
            <div style={{ marginTop: '10px' }}>
              {caseData.timeline.map((event) => (
                <div
                  key={event.id}
                  style={{
                    borderLeft: '3px solid #3b82f6',
                    paddingLeft: '10px',
                    marginBottom: '12px',
                  }}
                >
                  <div><strong>{event.action}</strong></div>
                  <div>{event.description}</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {event.performed_by || 'System'} • {event.created_at}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div style={{ marginTop: '20px' }}>
            <strong>Metadata</strong>
            <pre style={{ whiteSpace: 'pre-wrap', marginTop: '8px' }}>
{JSON.stringify(caseData.metadata || {}, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
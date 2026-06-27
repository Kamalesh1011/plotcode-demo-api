import { useEffect, useState, useRef } from 'react';
import { uploadFile, getUploads, deleteUpload, getUpload } from '../api';
import { toast } from '../components/Toast';

export default function FileUpload() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInput = useRef(null);

  const load = () => {
    setLoading(true);
    getUploads().then(d => { setFiles(d?.files || []); setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const handleFiles = async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    setUploading(true);
    for (const file of fileList) {
      const result = await uploadFile(file);
      if (result?.file) {
        toast('success', '✅ Uploaded', `${file.name} (${(file.size/1024).toFixed(1)} KB)`);
      } else {
        toast('error', '❌ Upload Failed', `Could not upload ${file.name}`);
      }
    }
    setUploading(false);
    load();
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const viewFile = async (id) => {
    const result = await getUpload(id);
    if (result?.file) {
      setPreview(result.file);
    } else {
      toast('error', '❌ Failed', 'Could not load file.');
    }
  };

  const remove = async (id) => {
    await deleteUpload(id);
    toast('info', '🗑️ Deleted', 'File removed.');
    if (preview?.id === id) setPreview(null);
    load();
  };

  const fmtSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024*1024) return `${(bytes/1024).toFixed(1)} KB`;
    return `${(bytes/1024/1024).toFixed(2)} MB`;
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">File Uploads</div>
      </div>

      {/* Upload Zone */}
      <div className="card mb-16">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => fileInput.current?.click()}
          style={{
            border: `2px dashed ${dragOver ? 'var(--primary)' : 'var(--border)'}`,
            borderRadius: 'var(--radius-lg)',
            padding: '40px 20px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s',
            background: dragOver ? 'rgba(124,58,237,0.05)' : 'transparent',
          }}
        >
          <div style={{ fontSize: 48, marginBottom: 12 }}>{uploading ? '⏳' : '📁'}</div>
          <div style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>
            {uploading ? 'Uploading…' : 'Drop files here or click to upload'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
            Code files, configs, logs · Max 10MB
          </div>
          <input
            ref={fileInput}
            type="file"
            multiple
            style={{ display: 'none' }}
            onChange={(e) => handleFiles(e.target.files)}
          />
        </div>
      </div>

      <div className="grid-2" style={{ alignItems: 'start' }}>
        {/* File List */}
        <div className="card">
          <div className="card-title">Uploaded Files ({files.length})</div>
          {loading ? (
            <div className="skeleton" style={{ height: 100 }} />
          ) : files.length === 0 ? (
            <div className="empty">
              <span className="empty-icon">📂</span>
              <div className="empty-title">No files uploaded</div>
              <div className="empty-desc">Upload code files above.</div>
            </div>
          ) : (
            files.map(f => (
              <div
                key={f.id}
                style={{
                  padding: '12px 0',
                  borderBottom: '1px solid var(--border)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                }}
              >
                <span style={{ fontSize: 20 }}>📄</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="font-mono text-sm" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {f.filename}
                  </div>
                  <div className="text-muted text-xs mt-4">
                    {fmtSize(f.size)} · {f.content_type} · by {f.uploaded_by} · {f.uploaded_at?.slice(0, 10)}
                  </div>
                </div>
                <button className="btn btn-ghost btn-sm" onClick={() => viewFile(f.id)}>👁️ View</button>
                <button className="btn btn-ghost btn-sm" onClick={() => remove(f.id)} style={{ color: 'var(--danger)' }}>🗑️</button>
              </div>
            ))
          )}
        </div>

        {/* File Preview */}
        <div className="card">
          <div className="card-title">File Preview</div>
          {!preview ? (
            <div className="empty">
              <span className="empty-icon">👁️</span>
              <div className="empty-title">No file selected</div>
              <div className="empty-desc">Click "View" on a file to see its content.</div>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: 12 }}>
                <div className="font-mono text-sm" style={{ fontWeight: 600 }}>{preview.filename}</div>
                <div className="text-muted text-xs mt-4">
                  {fmtSize(preview.size)} · {preview.content_type} · uploaded by {preview.uploaded_by}
                </div>
              </div>
              <pre className="plan-block" style={{ maxHeight: 500 }}>
                {preview.content || '(binary file — cannot display)'}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

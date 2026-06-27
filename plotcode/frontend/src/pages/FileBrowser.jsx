import { useEffect, useState } from 'react';
import { getRepos, getRepoContents, getFileContent } from '../api';

export default function FileBrowser() {
  const [repos, setRepos] = useState([]);
  const [selected, setSelected] = useState('');
  const [path, setPath] = useState('');
  const [items, setItems] = useState([]);
  const [fileContent, setFileContent] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getRepos().then(d => {
      const r = d?.repos || [];
      setRepos(r);
      if (r.length) setSelected(r[0].name);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    setLoading(true);
    setFileContent(null);
    getRepoContents(selected, path).then(d => { setItems(d?.items || []); setLoading(false); });
  }, [selected, path]);

  const openItem = (item) => {
    if (item.type === 'dir') {
      setPath(item.path);
    } else {
      getFileContent(selected, item.path).then(d => setFileContent(d));
    }
  };

  const goUp = () => {
    const parts = path.split('/').filter(Boolean);
    parts.pop();
    setPath(parts.join('/'));
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">File Browser</div>
        <select className="filter-select" value={selected} onChange={e => { setSelected(e.target.value); setPath(''); }}>
          {repos.map(r => <option key={r.name} value={r.name}>{r.name}</option>)}
        </select>
      </div>

      {/* Breadcrumb */}
      <div className="flex items-center gap-8 mb-16">
        <button className="btn btn-secondary btn-sm" onClick={() => setPath('')}>root</button>
        {path && <button className="btn btn-ghost btn-sm" onClick={goUp}>↑ up</button>}
        <span className="text-muted text-xs font-mono">{path || '/'}</span>
      </div>

      <div className="grid-1-2" style={{alignItems:'start'}}>
        <div className="card">
          <div className="card-title">Files</div>
          {loading ? <div className="skeleton" style={{height:200}}/> : (
            items.length === 0 ? <div className="text-muted text-sm">No files</div> :
            items.map(item => (
              <div className="file-tree-item" key={item.path} onClick={() => openItem(item)}>
                <span className="file-tree-icon">{item.type === 'dir' ? '📁' : '📄'}</span>
                <span>{item.name}</span>
              </div>
            ))
          )}
        </div>
        <div className="card">
          <div className="card-title">{fileContent ? fileContent.path : 'File Preview'}</div>
          {fileContent ? (
            <pre className="plan-block" style={{maxHeight:500, whiteSpace:'pre-wrap'}}>{fileContent.content}</pre>
          ) : (
            <div className="empty"><span className="empty-icon">📄</span><div className="empty-title">Select a file</div><div className="empty-desc">Click a file to view its content.</div></div>
          )}
        </div>
      </div>
    </div>
  );
}

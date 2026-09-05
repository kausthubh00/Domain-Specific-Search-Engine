import { useState } from 'react'
import './App.css'

function App() {
  // --- STATE VARIABLES ---
  const [query, setQuery] = useState('network');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  
  // UPLOAD STATE: Now expects an array/FileList of files
  const [selectedFiles, setSelectedFiles] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");

  // --- SEARCH LOGIC ---
  const handleSearch = async () => {
    setIsSearching(true);
    setHasSearched(false);
    
    try {
      const response = await fetch(`http://127.0.0.1:5000/api/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setResults(data);
    } catch (error) {
      console.error("Backend connection failed:", error);
    } finally {
      setIsSearching(false);
      setHasSearched(true);
    }
  }; 

  // --- BULK UPLOAD LOGIC ---
  const handleFileChange = (event) => {
    // Grabs ALL selected files instead of just the first one
    setSelectedFiles(event.target.files);
  };

  const handleUpload = async () => {
    if (!selectedFiles || selectedFiles.length === 0) {
        setUploadMessage("Please select at least one file first.");
        return;
    }

    const formData = new FormData();
    // Loop through all selected files and append them to the request
    for (let i = 0; i < selectedFiles.length; i++) {
        formData.append("file", selectedFiles[i]);
    }

    try {
        setUploadMessage(`Uploading ${selectedFiles.length} files...`);
        const response = await fetch("http://127.0.0.1:5000/api/upload", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();
        
        if (response.ok) {
            setUploadMessage(data.message); // Success!
        } else {
            setUploadMessage("Error: " + data.error);
        }
    } catch (error) {
        setUploadMessage("Failed to connect to the server.");
    }
  };

  // --- UI RENDER ---
  return (
    <div className="container">
        <div className="header">
            <h2>Domain-Specific Search</h2>
            <div className="status-badge">Nodes: 3 (Master + 2) | O(1) Indexing</div>
        </div>
        
        <div className="search-box">
            <input 
              type="text" 
              value={query} 
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter search query..."
            />
            <button onClick={handleSearch}>
                {isSearching ? 'SEARCHING...' : 'EXECUTE QUERY'}
            </button>
        </div>

        <div style={{ margin: "20px 0", padding: "15px", border: "1px dashed gray" }}>
         <h3>Upload Documents (Bulk)</h3>
          {/* THE MULTIPLE TAG IS ADDED HERE */}
          <input 
            type="file" 
            multiple 
            accept=".pdf,.docx,.txt" 
            onChange={handleFileChange} 
          />
          <button 
            onClick={handleUpload}
            style={{ marginLeft: "10px", padding: "5px 10px", cursor: "pointer" }}
          >
            Upload Files
          </button>
         <p style={{ color: "green", fontSize: "14px", marginTop: "10px" }}>{uploadMessage}</p>
        </div>

        {isSearching && <div className="metrics" style={{ color: '#e3b341' }}>&gt; Sending request to Flask API...</div>}

        {hasSearched && (
            <>
                <div className="metrics">
                    &gt; Found {results.length} results | Algorithm: TF-IDF | Memory: 42MB
                </div>

                <div id="results">
                    {results.map((result, index) => (
                        <div className="result" key={index}>
                            <h3 className="result-title">{result.title}</h3>
                            <p className="result-path">{result.path}</p>
                            <p className="result-snippet">{result.snippet}</p>
                            <div className="tags">
                                <span className="score-tag">{result.score}</span>
                                <span className="score-tag">{result.tag}</span>
                            </div>
                        </div>
                    ))}
                    {results.length === 0 && <p style={{color: '#8b949e'}}>No matching documents found in index.</p>}
                </div>
            </>
        )}
    </div>
  )
}

export default App
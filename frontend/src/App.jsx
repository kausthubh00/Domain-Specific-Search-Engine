import { useState } from 'react'
import './App.css'

function App() {
  // --- STATE VARIABLES ---
  const [query, setQuery] = useState('confidential compliance HIPAA protocols');
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadMessage, setUploadMessage] = useState("");

  // --- SEARCH LOGIC ---
  const handleSearch = async () => {
    setIsSearching(true);
    setHasSearched(false);
    
    try {
      // THIS IS THE REAL API BRIDGE: React talking to Python
      const response = await fetch(`http://127.0.0.1:5000/api/search?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      
      setResults(data);
    } catch (error) {
      console.error("Backend connection failed:", error);
    } finally {
      setIsSearching(false);
      setHasSearched(true);
    }
  }; // <-- THIS CLOSING BRACKET WAS MISSING!

  // --- UPLOAD LOGIC ---
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
        setUploadMessage("Please select a PDF first.");
        return;
    }

    // FormData is required when sending files over HTTP!
    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
        setUploadMessage("Uploading...");
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
         <h3>Upload New PDF</h3>
          <input 
            type="file" 
            accept="application/pdf" 
            onChange={handleFileChange} 
          />
          <button 
            onClick={handleUpload}
            style={{ marginLeft: "10px", padding: "5px 10px", cursor: "pointer" }}
          >
            Upload File
          </button>
         <p style={{ color: "green", fontSize: "14px" }}>{uploadMessage}</p>
        </div>

        {isSearching && <div className="metrics" style={{ color: '#e3b341' }}>&gt; Sending request to Flask API...</div>}

        {hasSearched && (
            <>
                <div className="metrics">
                    &gt; Found {results.length} results | Algorithm: TF-IDF Mock | Memory: 42MB
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
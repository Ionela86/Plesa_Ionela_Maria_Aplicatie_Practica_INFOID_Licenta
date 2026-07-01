import React, { useState } from "react";

function App() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      alert("Selectează un fișier PDF sau DOCX!");
      return;
    }

    const formData = new FormData();
    formData.append("file", file); // numele câmpului trebuie să fie "file" sau cum așteaptă backend-ul

    try {
      const response = await fetch("http://127.0.0.1:5000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Eroare la upload!");
      }

      const data = await response.json();
      setResult(JSON.stringify(data, null, 2));
    } catch (error) {
      console.error(error);
      setResult("A apărut o eroare la upload.");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h1>Smart Recrut - Upload CV</h1>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} style={{ marginLeft: "10px" }}>
        Trimite
      </button>
      {result && (
        <pre
          style={{
            marginTop: "20px",
            backgroundColor: "#f0f0f0",
            padding: "10px",
          }}
        >
          {result}
        </pre>
      )}
    </div>
  );
}

export default App;

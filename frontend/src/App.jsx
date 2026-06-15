import { useState } from "react";
import"./App.css";
import Header from "./components/Header";
import DrugInput from "./components/DrugInput";
import ResultCard from "./components/ResultCard";

function App() {

    const [drugs, setDrugs] = useState(["", ""]);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const checkInteraction = async () => {
        const filledDrugs = drugs.filter(d => d.trim() !== "");

        if (filledDrugs.length < 2) {
            setError("Please enter at least two medications.");
            return;
        }

        setLoading(true);
        setError(null);
        setResult(null)

        try {
            
            const params = filledDrugs.map(d => `drugs=${encodeURIComponent(d)}`).join("&");
            const response = await fetch(`http://127.0.0.1:8000/interact?${params}`);
            const data = await response.json();

            if (data.error) {
                setError(data.error);
            } else {
                setResult(data);
            }
        } catch (err) {
            setError("Could not connect to Contraxa API. Make sure the server is still running.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="app">
            <Header />
            <main className="main">
                <DrugInput
                drugs={drugs}
                setDrugs={setDrugs}
                onCheck={checkInteraction}
                loading={loading}
                />
            {error && <p className="error">{error}</p>}
            {result && <ResultCard result={result} />}
            </main>
        </div>
    );
}

export default App
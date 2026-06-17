function DrugInput({ drugs, setDrugs, onCheck, loading }) {
    const handleChange = (index, value) => {
        const updated = [...drugs];
        updated[index] = value;
        setDrugs(updated);
    };

    const addDrug = () => {
        if (drugs.length < 5) {
            setDrugs([...drugs, ""]);
        }
    };

    return (
        <section className="input-section">
            <p className="input-subtitle">Checking interactions for human medications</p>
            <p className="input-label">ENTER MEDICATIONS TO CHECK</p>

            <div className="inputs">
                {drugs.map((drug, index) => (
                    <input 
                    key={index}
                    type="text"
                    className="drug-input"
                    placeholder={`Medication ${index + 1}`}
                    value={drug}
                    onChange={(e) => handleChange(index, e.target.value)}
                    />
                ))}
            </div>

            <div className="action-row">
                {drugs.length < 5 && (
                    <button className="add-btn" onClick={addDrug}>+</button>
                )}

                <button 
                className="check-btn"
                onClick={onCheck}
                disabled={loading}
                >🔬 {loading ? "Analyzing..." : "Check Interactions"}</button>
            </div>

        </section>
    );
}

export default DrugInput;
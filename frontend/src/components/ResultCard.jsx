function ResultCard({ result }) {
  const { analysis } = result;

  const getSeverityClass = () => {
    if (analysis.severity === "danger") return "badge-danger";
    if (analysis.severity === "caution") return "badge-caution";
    return "badge-safe";
  };

  return (
    <div className="result-card">
      <div className={`severity-badge ${getSeverityClass()}`}>
        {analysis.severity.toUpperCase()}
      </div>

      <div className="card-section">
        <p className="section-label">Interaction</p>
        <p className="section-text">{analysis.summary}</p>
      </div>

      <div className="card-section">
        <p className="section-label">Flags Detected</p>

        <div className="flags">
          {analysis.flags.map((flag, index) => (
            <span key={index} className="flag-chip">
              {flag}
            </span>
          ))}
        </div>
      </div>

      <p className="disclaimer">
        Always consult your healthcare provider or vetinarian before making
        changes to any medication.
      </p>
    </div>
  );
}

export default ResultCard;

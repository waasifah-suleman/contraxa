import { useState, useEffect } from "react";

function ResultCard({ result }) {
  const { analysis, drugs } = result;

  // this state holds the text we progressively reveal for the typing effect
  const [displayedSummary, setDisplayedSummary] = useState("");

  // this effect runs whenever the summary changes and types it out letter by letter
  useEffect(() => {
    setDisplayedSummary("");
    let index = 0;
    const fullText = analysis.summary;

    // setInterval runs a function repeatedly every X milliseconds
    const interval = setInterval(() => {
      index++;
      // slicing the full text up to the current index, growing it one character at a time
      setDisplayedSummary(fullText.slice(0, index));

      // once we've revealed the whole text, stop the interval
      if (index >= fullText.length) {
        clearInterval(interval);
      }
    }, 15);

    // cleanup function - clears the interval if the component unmounts mid-typing
    return () => clearInterval(interval);
  }, [analysis.summary]);

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
        {displayedSummary.split('\n\n').map((line, i) => (
          <p key={i} className="section-text">{line}</p>
        ))}
      </div>

      <div className="card-section">
        <p className="section-label">Active Ingredients</p>
        <div className="ingredient-chips">
          {/* looping through each drug to show its active ingredient as a chip */}
          {drugs.map((drug, index) => (
            <span key={index} className="ingredient-chip">
              {drug.active_ingredients}
            </span>
          ))}
        </div>
      </div>

      <div className="card-section">
        <p className="section-label">Side Effects</p>
        {/* checking if any drug actually has side effects to show */}
        {drugs.some((d) => d.side_effects.length > 0) ? (
          <ul className="side-effects-list">
            {/* flattening all side effects from all drugs into one list */}
            {drugs
              .flatMap((d) => d.side_effects)
              .map((effect, index) => (
                <li key={index}>{effect}</li>
              ))}
          </ul>
        ) : (
          <p className="section-text">
            No specific side effects listed for these medications.
          </p>
        )}
      </div>

      <p className="disclaimer">
        Always consult your healthcare provider or veterinarian before making
        changes to any medication.
      </p>
    </div>
  );
}

export default ResultCard;

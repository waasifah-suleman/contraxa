function Header() {
    return (
        <header className="header">
            <div className="header-left">
                <span  className="logo">C</span>
                <h1 className="brand">Contraxa</h1>
            </div>
            <div className="toggle">
                <button className="toggle-btn active">👤 People</button>
                <button className="toggle-btn">🐾 Pets</button>
            </div>
        </header>
    );
}

export default Header;
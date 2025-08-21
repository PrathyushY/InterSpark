import React, { useState } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Footer } from './components/layout/Footer';
import { Home } from './pages/Home';
import { Dashboard } from './pages/Dashboard';
import { Login } from './pages/Login';
import { Signup } from './pages/Signup';
import { Profile } from './pages/Profile';
import { OpportunityDetails } from './pages/OpportunityDetails';
import { Opportunities } from './pages/Opportunities';
import { TalentSearch } from './pages/TalentSearch';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
export function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  // Mock login/logout functions
  const handleLogin = () => setIsLoggedIn(true);
  const handleLogout = () => setIsLoggedIn(false);
  return <BrowserRouter>
      <div className="flex flex-col min-h-screen bg-gray-50">
        <Navbar isLoggedIn={isLoggedIn} onLogout={handleLogout} />
        <main className="flex-grow">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            <Route path="/signup" element={<Signup onLogin={handleLogin} />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/opportunities" element={<Opportunities />} />
            <Route path="/opportunity/:id" element={<OpportunityDetails />} />
            <Route path="/talent" element={<TalentSearch />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>;
}
import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
import DestinationCard from './DestinationCard';

const DestinationGrid = ({
  destinations = [],
  language,
  onSelectDestination,
  kicker,
  title,
  description
}) => {
  const [showAll, setShowAll] = useState(false);
  const isVi = language === 'vi';

  // Filter to only featured destinations for default view
  const featuredDestinations = destinations.filter(d => d.featured);
  
  // Decide which list to render
  const displayedDestinations = showAll ? destinations : featuredDestinations;

  const toggleShowAll = () => {
    setShowAll(prev => !prev);
  };

  return (
    <section className="destination-section" id="places" aria-labelledby="destination-section-title">
      <div className="destination-section-heading">
        <span className="section-label">{kicker}</span>
        <h2 id="destination-section-title">{title}</h2>
        <p>{description}</p>
      </div>

      <div className="destination-grid">
        {displayedDestinations.map((destination) => (
          <DestinationCard
            key={destination.id}
            destination={destination}
            language={language}
            onSelect={onSelectDestination}
          />
        ))}
      </div>

      {destinations.length > featuredDestinations.length && (
        <div className="destination-toggle-container">
          <button
            type="button"
            className="destination-toggle-btn"
            onClick={toggleShowAll}
            aria-expanded={showAll}
          >
            <span>
              {showAll 
                ? (isVi ? 'Thu gọn' : 'View less') 
                : (isVi ? 'Xem tất cả địa điểm' : 'View all stops')
              }
            </span>
            {showAll ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      )}
    </section>
  );
};

export default DestinationGrid;

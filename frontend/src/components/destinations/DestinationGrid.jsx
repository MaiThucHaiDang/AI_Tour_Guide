import React from 'react';
import DestinationCard from './DestinationCard';

const DestinationGrid = ({
  destinations,
  language,
  onSelectDestination,
  kicker,
  title,
  description
}) => (
  <section className="destination-section" id="places" aria-labelledby="destination-section-title">
    <div className="destination-section-heading">
      <span className="section-label">{kicker}</span>
      <h2 id="destination-section-title">{title}</h2>
      <p>{description}</p>
    </div>

    <div className="destination-grid">
      {destinations.map((destination) => (
        <DestinationCard
          key={destination.id}
          destination={destination}
          language={language}
          onSelect={onSelectDestination}
        />
      ))}
    </div>
  </section>
);

export default DestinationGrid;

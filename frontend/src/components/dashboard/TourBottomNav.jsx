import React from 'react';

const TourBottomNav = ({ tabs, activeTab, setActiveTab, isVi, onPreloadChat }) => {
  return (
    <nav className="tour-bottom-nav" aria-label={isVi ? 'Điều hướng tham quan' : 'Tour navigation'}>
      {tabs.map(({ key, label, icon: Icon }) => (
        <button
          key={key}
          className={activeTab === key ? 'active' : ''}
          onClick={() => {
            if (key === 'ask') onPreloadChat?.();
            setActiveTab(key);
          }}
          onMouseEnter={() => {
            if (key === 'ask') onPreloadChat?.();
          }}
          onFocus={() => {
            if (key === 'ask') onPreloadChat?.();
          }}
          aria-current={activeTab === key ? 'page' : undefined}
        >
          <Icon size={21} />
          <span>{label}</span>
        </button>
      ))}
    </nav>
  );
};

export default TourBottomNav;

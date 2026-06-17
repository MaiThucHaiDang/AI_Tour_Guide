import React from 'react';
import { Sparkles } from 'lucide-react';

const QuickPromptChips = ({
  prompts,
  onPromptClick,
  language
}) => {
  const isVi = language === 'vi';
  if (!prompts || prompts.length === 0) return null;

  return (
    <div className="quick-prompt-chips-wrapper">
      <div className="chips-label">
        <Sparkles size={12} className="chips-icon" />
        <span>{isVi ? 'Gợi ý hỏi nhanh:' : 'Suggested questions:'}</span>
      </div>
      <div className="quick-prompt-chips-scroll">
        {prompts.map((prompt, index) => (
          <button 
            key={`${prompt}-${index}`} 
            className="quick-prompt-chip"
            onClick={() => onPromptClick(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
};

export default QuickPromptChips;

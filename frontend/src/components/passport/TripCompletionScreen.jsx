import React from 'react';
import { ArrowLeft, CheckCircle2, Home, Share2 } from 'lucide-react';
import TripJournal from './TripJournal';
import { buildTourSummary } from '../../services/tourMemoryService';

const TripCompletionScreen = ({
  language,
  catalog,
  memory,
  onBackToTour,
  onBackHome,
  onResetMemory
}) => {
  const isVi = language === 'vi';
  const summary = buildTourSummary(memory, catalog, language);

  return (
    <div className="trip-completion-screen" role="dialog" aria-modal="true">
      <header className="trip-completion-header">
        <button type="button" onClick={onBackToTour} className="trip-completion-back">
          <ArrowLeft size={19} />
          <span>{isVi ? 'Quay lại tour' : 'Back to tour'}</span>
        </button>

        <div className="trip-completion-title">
          <span>{isVi ? 'Đã kết thúc chuyến đi' : 'Trip completed'}</span>
          <h1>{isVi ? 'Nhật ký Đại Nội của bạn' : 'Your Imperial City journal'}</h1>
        </div>

        <button type="button" onClick={onBackHome} className="trip-completion-home">
          <Home size={18} />
          <span>{isVi ? 'Trang chủ' : 'Home'}</span>
        </button>
      </header>

      <section className="trip-completion-summary" aria-label={isVi ? 'Tóm tắt chuyến đi' : 'Trip summary'}>
        <article>
          <CheckCircle2 size={22} />
          <span>{isVi ? 'Dấu mộc đã nhận' : 'Stamps collected'}</span>
          <strong>{summary.completedCount}/{summary.totalCount}</strong>
        </article>
        <article>
          <Share2 size={22} />
          <span>{isVi ? 'Nội dung nhật ký' : 'Journal items'}</span>
          <strong>{summary.photos.length + summary.questions.length + summary.audio.length}</strong>
        </article>
      </section>

      <main className="trip-completion-body">
        <TripJournal
          language={language}
          catalog={catalog}
          memory={memory}
          onResetMemory={onResetMemory}
        />
      </main>
    </div>
  );
};

export default TripCompletionScreen;

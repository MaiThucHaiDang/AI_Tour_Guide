import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Gamepad2, Award, CheckCircle2, XCircle, Timer, Loader2 } from 'lucide-react';
import { joinGameRoomAPI, getGameRoomStatusAPI, submitAnswerAPI } from '../../services/apiService';

const GamePlayer = ({ roomCode, language, onBack }) => {
  const isVi = language === 'vi';
  const [nickname, setNickname] = useState('');
  const [isJoined, setIsJoined] = useState(false);
  const [roomState, setRoomState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  
  // Player state within the active game
  const [selectedOption, setSelectedOption] = useState(null);
  const [answerResult, setAnswerResult] = useState(null); // { is_correct, score_awarded, total_score }
  const [hasAnswered, setHasAnswered] = useState(false);
  const [timerVal, setTimerVal] = useState(30);

  const prevStatusRef = useRef('lobby');
  const prevQuestionIndexRef = useRef(0);

  // Poll room status every 1.5 seconds once joined
  useEffect(() => {
    if (!isJoined || !roomCode) return;

    const fetchStatus = async () => {
      try {
        const res = await getGameRoomStatusAPI(roomCode);
        if (res.success && res.room) {
          const room = res.room;
          setRoomState(room);

          // Reset answering state if question advances
          if (room.status === 'playing') {
            if (prevStatusRef.current !== 'playing' || prevQuestionIndexRef.current !== room.current_question_index) {
              setHasAnswered(false);
              setSelectedOption(null);
              setAnswerResult(null);
              prevQuestionIndexRef.current = room.current_question_index;
            }
            if (room.current_question?.seconds_remaining) {
              setTimerVal(Math.ceil(room.current_question.seconds_remaining));
            }
          }
          prevStatusRef.current = room.status;
        }
      } catch (err) {
        console.error('Error polling room status:', err);
      }
    };

    fetchStatus(); // initial fetch
    const intervalId = setInterval(fetchStatus, 1500);
    return () => clearInterval(intervalId);
  }, [isJoined, roomCode]);

  // Handle local countdown timer for active questions
  useEffect(() => {
    if (roomState?.status !== 'playing' || hasAnswered) return;
    if (timerVal <= 0) return;

    const tId = setTimeout(() => {
      setTimerVal(prev => prev - 1);
    }, 1000);
    return () => clearTimeout(tId);
  }, [timerVal, roomState?.status, hasAnswered]);

  const handleJoin = async (e) => {
    e.preventDefault();
    if (!nickname.trim()) return;

    try {
      setLoading(true);
      setErrorMsg('');
      const res = await joinGameRoomAPI(roomCode, nickname.trim());
      if (res.success) {
        setIsJoined(true);
        // Fetch initial state
        const statusRes = await getGameRoomStatusAPI(roomCode);
        if (statusRes.success) {
          setRoomState(statusRes.room);
        }
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || (isVi ? 'Không thể tham gia phòng chơi.' : 'Failed to join game room.'));
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = async (optIdx) => {
    if (hasAnswered || roomState?.status !== 'playing') return;
    
    setSelectedOption(optIdx);
    setHasAnswered(true);

    try {
      const res = await submitAnswerAPI(
        roomCode,
        nickname.trim(),
        roomState.current_question.question_index,
        optIdx
      );
      if (res.success) {
        setAnswerResult({
          is_correct: res.is_correct,
          score_awarded: res.score_awarded,
          total_score: res.total_score
        });
      }
    } catch (err) {
      console.error('Error submitting answer:', err);
    }
  };

  // Find player status in list
  const currentPlayerInfo = roomState?.players?.find(p => p.nickname === nickname.trim());
  const playerRank = roomState?.players?.findIndex(p => p.nickname === nickname.trim()) + 1;

  // Shapes & Colors for options (similar to Kahoot)
  const optionStyles = [
    { bg: 'linear-gradient(135deg, #e21b3c, #b00b24)', shape: '▲', colorName: 'Red' },
    { bg: 'linear-gradient(135deg, #1368ce, #0d4b96)', shape: '◆', colorName: 'Blue' },
    { bg: 'linear-gradient(135deg, #d89e00, #b08000)', shape: '●', colorName: 'Yellow' },
    { bg: 'linear-gradient(135deg, #26890c, #1b6108)', shape: '■', colorName: 'Green' }
  ];

  return (
    <div className="mobile-tour-shell" style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#f4f6f8' }}>
      
      {/* Header */}
      <header className="tour-shell-header">
        <button className="tour-shell-back" onClick={onBack} aria-label="Trở lại">
          <ArrowLeft size={20} />
        </button>
        <div className="tour-shell-title">
          <span>{isVi ? 'Đấu Trí Cung Đình' : 'Citadel Quiz Show'}</span>
          <h1>{isVi ? `Phòng: ${roomCode}` : `Room: ${roomCode}`}</h1>
        </div>
        <div style={{ width: 40 }} />
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: '20px', display: 'flex', flexDirection: 'column', overflowY: 'auto', position: 'relative' }}>
        
        {/* Step 1: Join Room Nickname Form */}
        {!isJoined && (
          <div style={{
            margin: 'auto 0',
            backgroundColor: '#ffffff',
            borderRadius: '24px',
            padding: '24px',
            boxShadow: '0 8px 32px rgba(15, 95, 89, 0.08)',
            border: '1px solid rgba(15, 95, 89, 0.1)',
            textAlign: 'center'
          }}>
            <div style={{
              width: '60px', height: '60px', borderRadius: '18px',
              background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
              display: 'grid', placeItems: 'center', margin: '0 auto 16px auto',
              boxShadow: '0 8px 20px rgba(15,95,89,0.2)'
            }}>
              <Gamepad2 size={28} color="#fff" />
            </div>

            <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#0f5f59', marginBottom: '8px' }}>
              {isVi ? 'Đấu Trí Cung Đình' : 'Citadel Game Lobby'}
            </h2>
            <p style={{ fontSize: '13px', color: '#666', marginBottom: '20px' }}>
              {isVi 
                ? 'Nhập một biệt danh cá tính để bắt đầu đấu trí cùng nhóm bạn.'
                : 'Enter a nickname to join the trivia room with your friends.'}
            </p>

            <form onSubmit={handleJoin} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <input
                type="text"
                maxLength={20}
                required
                placeholder={isVi ? 'Biệt danh của bạn...' : 'Your nickname...'}
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                style={{
                  padding: '14px 16px',
                  borderRadius: '12px',
                  border: '1.5px solid #ddd',
                  fontSize: '15px',
                  outline: 'none',
                  textAlign: 'center',
                  fontWeight: '600'
                }}
              />

              {errorMsg && (
                <div style={{ color: '#d32f2f', fontSize: '12px', fontWeight: '600' }}>
                  {errorMsg}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: '14px',
                  borderRadius: '12px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
                  color: '#fff',
                  fontSize: '15px',
                  fontWeight: '700',
                  cursor: 'pointer',
                  boxShadow: '0 4px 15px rgba(15, 95, 89, 0.25)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px'
                }}
              >
                {loading ? <Loader2 className="spin" size={18} /> : null}
                {isVi ? 'THAM GIA NGAY' : 'JOIN NOW'}
              </button>
            </form>
          </div>
        )}

        {/* Step 2: Lobby Screen (Waiting for Host to start) */}
        {isJoined && roomState?.status === 'lobby' && (
          <div style={{
            margin: 'auto 0',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{
              width: '80px', height: '80px', borderRadius: '50%',
              backgroundColor: '#e6f4ea', color: '#137333',
              display: 'grid', placeItems: 'center',
              animation: 'pulse 2s infinite'
            }}>
              <CheckCircle2 size={40} />
            </div>

            <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#0f5f59', margin: 0 }}>
              {isVi ? `Chào mừng ${nickname}!` : `Welcome ${nickname}!`}
            </h3>
            <p style={{ fontSize: '14px', color: '#666', margin: 0, maxWidth: '280px', lineHeight: '1.4' }}>
              {isVi 
                ? 'Bạn đã tham gia phòng thành công! Hãy đợi trưởng nhóm bấm nút bắt đầu cuộc chơi.'
                : 'Joined successfully! Please wait for the host to start the game.'}
            </p>

            <div style={{
              backgroundColor: '#fff',
              border: '1px solid #e0e0e0',
              borderRadius: '12px',
              padding: '10px 20px',
              fontSize: '13px',
              color: '#555',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <Loader2 className="spin" size={14} />
              {isVi ? 'Đang đợi bắt đầu...' : 'Waiting for host...'}
            </div>
          </div>
        )}

        {/* Step 3: Question Answer Controller (Active Game) */}
        {isJoined && roomState?.status === 'playing' && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '16px' }}>
            
            {/* Top row status */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '13px', fontWeight: '700', color: '#555' }}>
                {isVi ? `Câu hỏi ${roomState.current_question.question_index + 1}/${roomState.total_questions}` : `Question ${roomState.current_question.question_index + 1}/${roomState.total_questions}`}
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: timerVal <= 5 ? '#d32f2f' : '#0f5f59', fontWeight: '700', fontSize: '14px' }}>
                <Timer size={16} />
                <span>{timerVal}s</span>
              </div>
            </div>

            {/* Question Text block */}
            <div style={{
              backgroundColor: '#fff', borderRadius: '16px', padding: '16px',
              border: '1px solid #eef2f5', textAlign: 'center',
              boxShadow: '0 2px 8px rgba(0,0,0,0.02)', margin: '4px 0'
            }}>
              <h3 style={{ fontSize: '15px', fontWeight: '800', color: '#333', margin: 0, lineHeight: '1.4' }}>
                {roomState.current_question.question_text}
              </h3>
            </div>

            {/* Answer Options Grid */}
            {!hasAnswered ? (
              <div style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
                minHeight: '280px'
              }}>
                {optionStyles.map((style, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectOption(idx)}
                    style={{
                      border: 'none',
                      borderRadius: '16px',
                      background: style.bg,
                      color: 'white',
                      fontSize: '14px',
                      fontWeight: '700',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-start',
                      padding: '12px 16px',
                      boxShadow: '0 4px 10px rgba(0,0,0,0.1)',
                      transition: 'transform 0.1s active',
                      textAlign: 'left',
                      lineHeight: '1.4',
                      wordBreak: 'break-word',
                      gap: '12px',
                      width: '100%',
                      minHeight: '60px'
                    }}
                  >
                    <span style={{ fontSize: '20px', fontWeight: '900', flexShrink: 0 }}>{style.shape}</span>
                    <span>{roomState.current_question.options[idx]}</span>
                  </button>
                ))}
              </div>
            ) : (
              /* Waiting Screen after player chooses an option */
              <div style={{
                flex: 1,
                backgroundColor: '#ffffff',
                borderRadius: '24px',
                padding: '24px',
                boxShadow: '0 8px 32px rgba(0,0,0,0.05)',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '16px',
                textAlign: 'center'
              }}>
                {selectedOption !== null && (
                  <div style={{
                    padding: '14px 20px',
                    borderRadius: '16px',
                    background: optionStyles[selectedOption].bg,
                    color: 'white',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    fontWeight: '700',
                    fontSize: '14px',
                    width: '100%',
                    maxWidth: '320px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
                    textAlign: 'left',
                    wordBreak: 'break-word',
                    lineHeight: '1.4'
                  }}>
                    <span style={{ fontSize: '20px', fontWeight: '900', flexShrink: 0 }}>{optionStyles[selectedOption].shape}</span>
                    <span>{roomState.current_question.options[selectedOption]}</span>
                  </div>
                )}
                <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#333', margin: 0 }}>
                  {isVi ? 'Đã nhận câu trả lời!' : 'Answer received!'}
                </h3>
                <p style={{ fontSize: '13px', color: '#666', margin: 0 }}>
                  {isVi ? 'Hãy theo dõi màn hình chính để xem đáp án.' : 'Watch the host screen for results.'}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#999', marginTop: '10px' }}>
                  <Loader2 className="spin" size={14} />
                  <span>{isVi ? 'Chờ người chơi khác...' : 'Waiting for others...'}</span>
                </div>
              </div>
            )}
            
            {/* Player's Current Score Footer */}
            <div style={{
              backgroundColor: '#fff', borderRadius: '12px', padding: '12px 16px',
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              border: '1px solid #e0e0e0'
            }}>
              <span style={{ fontSize: '12px', color: '#666' }}>{isVi ? 'Tổng điểm hiện tại:' : 'Current Score:'}</span>
              <strong style={{ fontSize: '16px', color: '#b2820a' }}>{currentPlayerInfo?.score || 0} pts</strong>
            </div>
          </div>
        )}

        {/* Step 4: Scoreboard Step feedback (Show result) */}
        {isJoined && roomState?.status === 'scoreboard' && (
          <div style={{
            margin: 'auto 0',
            backgroundColor: '#ffffff',
            borderRadius: '24px',
            padding: '28px 24px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.06)',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px'
          }}>
            {answerResult ? (
              answerResult.is_correct ? (
                <>
                  <div style={{ color: '#2e7d32', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                    <CheckCircle2 size={56} />
                    <h3 style={{ fontSize: '20px', fontWeight: '800', margin: 0 }}>
                      {isVi ? 'CHÍNH XÁC!' : 'CORRECT!'}
                    </h3>
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: '800', color: '#2e7d32' }}>
                    +{answerResult.score_awarded} {isVi ? 'điểm' : 'pts'}
                  </div>
                </>
              ) : (
                <>
                  <div style={{ color: '#d32f2f', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                    <XCircle size={56} />
                    <h3 style={{ fontSize: '20px', fontWeight: '800', margin: 0 }}>
                      {isVi ? 'SAI MẤT RỒI!' : 'INCORRECT!'}
                    </h3>
                  </div>
                  <p style={{ fontSize: '13px', color: '#666', margin: 0 }}>
                    {isVi ? 'Không sao cả, hãy cố gắng ở câu tiếp theo nhé!' : 'Keep going! Try to get the next one.'}
                  </p>
                </>
              )
            ) : (
              /* If player didn't answer in time */
              <>
                <div style={{ color: '#f57c00', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
                  <Timer size={56} />
                  <h3 style={{ fontSize: '20px', fontWeight: '800', margin: 0 }}>
                    {isVi ? 'HẾT GIỜ!' : 'TIME UP!'}
                  </h3>
                </div>
                <p style={{ fontSize: '13px', color: '#666', margin: 0 }}>
                  {isVi ? 'Bạn đã không đưa ra câu trả lời kịp thời.' : "You didn't submit an answer in time."}
                </p>
              </>
            )}

            <div style={{
              width: '100%', borderTop: '1px solid #eee', paddingTop: '16px',
              marginTop: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <div style={{ textAlign: 'left' }}>
                <span style={{ fontSize: '11px', color: '#999', display: 'block' }}>{isVi ? 'Thứ hạng hiện tại' : 'Current Rank'}</span>
                <strong style={{ fontSize: '18px', color: '#0f5f59' }}>#{playerRank || '-'}</strong>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '11px', color: '#999', display: 'block' }}>{isVi ? 'Tổng số điểm' : 'Total Score'}</span>
                <strong style={{ fontSize: '18px', color: '#b2820a' }}>{currentPlayerInfo?.score || 0} pts</strong>
              </div>
            </div>
            
            <div style={{ fontSize: '12px', color: '#888', fontStyle: 'italic', marginTop: '10px' }}>
              {isVi ? 'Chờ trưởng nhóm chuyển sang câu tiếp theo...' : 'Waiting for host to continue...'}
            </div>
          </div>
        )}

        {/* Step 5: Finished Screen (Show final podium place) */}
        {isJoined && roomState?.status === 'finished' && (
          <div style={{
            margin: 'auto 0',
            backgroundColor: '#ffffff',
            borderRadius: '24px',
            padding: '32px 24px',
            boxShadow: '0 8px 32px rgba(15, 95, 89, 0.08)',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{
              width: '70px', height: '70px', borderRadius: '50%',
              backgroundColor: playerRank === 1 ? '#fff8e1' : '#f5f5f5',
              color: playerRank === 1 ? '#ffb300' : '#555',
              display: 'grid', placeItems: 'center', boxShadow: '0 4px 10px rgba(0,0,0,0.05)'
            }}>
              <Award size={36} />
            </div>

            <h3 style={{ fontSize: '20px', fontWeight: '800', color: '#0f5f59', margin: 0 }}>
              {isVi ? 'TRÒ CHƠI KẾT THÚC!' : 'GAME OVER!'}
            </h3>

            <div style={{ margin: '8px 0' }}>
              <span style={{ fontSize: '12px', color: '#888', display: 'block' }}>{isVi ? 'Xếp hạng của bạn' : 'Your final rank'}</span>
              <strong style={{ fontSize: '42px', fontWeight: '900', color: playerRank === 1 ? '#ffb300' : '#0f5f59', display: 'block' }}>
                #{playerRank || '-'}
              </strong>
            </div>

            <div style={{
              backgroundColor: '#f8f9fa', borderRadius: '12px', padding: '10px 20px',
              fontSize: '14px', fontWeight: '700', color: '#b2820a'
            }}>
              {isVi ? `Tổng điểm: ${currentPlayerInfo?.score || 0} điểm` : `Final Score: ${currentPlayerInfo?.score || 0} pts`}
            </div>

            <p style={{ fontSize: '13px', color: '#666', lineHeight: '1.4', margin: '8px 0 0 0' }}>
              {playerRank === 1
                ? (isVi ? '🎉 Thật xuất sắc! Bạn đã đánh bại tất cả để dẫn đầu cuộc chơi!' : '🎉 Amazing! You have won the game!')
                : (isVi ? 'Cảm ơn bạn đã tham gia! Hãy nghe AI tổng kết cuộc đấu.' : 'Thank you for playing! Check host screen for summary.')}
            </p>

            <button
              onClick={onBack}
              style={{
                width: '100%',
                padding: '12px',
                borderRadius: '10px',
                border: 'none',
                backgroundColor: '#0f5f59',
                color: '#fff',
                fontWeight: '700',
                fontSize: '14px',
                cursor: 'pointer',
                marginTop: '16px'
              }}
            >
              {isVi ? 'Quay lại bản đồ' : 'Back to map'}
            </button>
          </div>
        )}

      </main>
    </div>
  );
};

export default GamePlayer;

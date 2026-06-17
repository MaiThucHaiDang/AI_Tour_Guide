import React, { useState, useEffect, useRef } from 'react';
import { Play, Navigation, Users, Trophy, ChevronRight, X, Volume2, Sparkles, Loader2, QrCode, AlertCircle, MessageSquare } from 'lucide-react';
import { startGameAPI, getGameRoomStatusAPI, nextQuestionAPI, endGameAPI, getGameRoomPraiseAPI, playTTS, stopTTS, getLocalIpAPI } from '../../services/apiService';

const GameHost = ({ roomCode, language, onBack, onMinimize }) => {
  const isVi = language === 'vi';
  const [roomState, setRoomState] = useState(null);
  const [loading, setLoading] = useState(false);
  const [praiseText, setPraiseText] = useState('');
  const [loadingPraise, setLoadingPraise] = useState(false);
  const [audioUtterance, setAudioUtterance] = useState(null);
  const [localIp, setLocalIp] = useState('127.0.0.1');

  // Fetch local LAN IP from backend on mount
  useEffect(() => {
    const fetchLocalIp = async () => {
      try {
        const res = await getLocalIpAPI();
        if (res.success && res.local_ip) {
          setLocalIp(res.local_ip);
        }
      } catch (err) {
        console.error('Error fetching local IP:', err);
      }
    };
    fetchLocalIp();
  }, []);

  // Poll room status every 1.5 seconds
  useEffect(() => {
    if (!roomCode) return;

    const fetchStatus = async () => {
      try {
        const res = await getGameRoomStatusAPI(roomCode);
        if (res.success && res.room) {
          setRoomState(res.room);
        }
      } catch (err) {
        console.error('Error fetching host room status:', err);
      }
    };

    fetchStatus();
    const intervalId = setInterval(fetchStatus, 1500);
    return () => clearInterval(intervalId);
  }, [roomCode]);

  // Load AI praise speech once game is finished
  useEffect(() => {
    if (roomState?.status !== 'finished' || !roomCode || praiseText) return;

    const fetchPraise = async () => {
      try {
        setLoadingPraise(true);
        const res = await getGameRoomPraiseAPI(roomCode);
        if (res.success && res.praise) {
          setPraiseText(res.praise);
          // Play the praise text using TTS automatically
          const utterance = playTTS(res.praise, language);
          setAudioUtterance(utterance);
        }
      } catch (err) {
        console.error('Error fetching AI victory praise:', err);
      } finally {
        setLoadingPraise(false);
      }
    };

    fetchPraise();
  }, [roomState?.status, roomCode, praiseText, language]);

  // Stop TTS on unmount
  useEffect(() => {
    return () => {
      stopTTS();
    };
  }, []);

  // Auto-advance to scoreboard when time expires
  useEffect(() => {
    if (roomState?.status === 'playing' && roomState.current_question) {
      const remaining = roomState.current_question.seconds_remaining;
      if (remaining <= 0 && !loading) {
        handleNext();
      }
    }
  }, [roomState?.status, roomState?.current_question?.seconds_remaining, loading]);

  const handleStart = async () => {
    if (!roomCode || roomState?.players?.length === 0) return;
    try {
      setLoading(true);
      const res = await startGameAPI(roomCode);
      if (res.success) {
        setRoomState(res.room);
      }
    } catch (err) {
      console.error('Failed to start game:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNext = async () => {
    if (!roomCode) return;
    try {
      setLoading(true);
      const res = await nextQuestionAPI(roomCode);
      if (res.success) {
        setRoomState(res.room);
      }
    } catch (err) {
      console.error('Failed to advance game:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleEnd = async () => {
    if (!roomCode) return;
    try {
      setLoading(true);
      const res = await endGameAPI(roomCode);
      if (res.success) {
        setRoomState(res.room);
      }
    } catch (err) {
      console.error('Failed to end game:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSpeakPraise = () => {
    if (praiseText) {
      stopTTS();
      const utterance = playTTS(praiseText, language);
      setAudioUtterance(utterance);
    }
  };

  if (!roomState) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '12px' }}>
        <Loader2 className="spin" size={32} color="#0f5f59" />
        <span style={{ fontSize: '14px', color: '#666' }}>{isVi ? 'Đang khởi tạo phòng chơi...' : 'Initializing game room...'}</span>
      </div>
    );
  }

  // Build join link, automatically replacing localhost with LAN IP if necessary
  const getJoinLink = () => {
    const origin = window.location.origin;
    const hostname = window.location.hostname;
    const isLocalhost = hostname === 'localhost' || hostname === '127.0.0.1';
    
    if (isLocalhost && localIp && localIp !== '127.0.0.1') {
      return origin.replace(hostname, localIp) + `/?view=join&code=${roomCode}`;
    }
    return origin + `/?view=join&code=${roomCode}`;
  };

  const joinLink = getJoinLink();
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=${encodeURIComponent(joinLink)}`;

  // Shapes & Colors for options
  const optionStyles = [
    { bg: 'linear-gradient(135deg, #e21b3c, #b00b24)', shape: '▲', colorName: 'Red' },
    { bg: 'linear-gradient(135deg, #1368ce, #0d4b96)', shape: '◆', colorName: 'Blue' },
    { bg: 'linear-gradient(135deg, #d89e00, #b08000)', shape: '●', colorName: 'Yellow' },
    { bg: 'linear-gradient(135deg, #26890c, #1b6108)', shape: '■', colorName: 'Green' }
  ];

  return (
    <div style={{
      width: '100%', height: '100%', display: 'flex', flexDirection: 'column',
      backgroundColor: '#f7f9fb', position: 'relative'
    }}>
      
      {/* Lobby Header */}
      <div style={{
        padding: '16px 20px', borderBottom: '1px solid #eef2f5',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        backgroundColor: '#fff'
      }}>
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '800', color: '#0f5f59' }}>
            👑 {isVi ? 'Đấu Trí Cung Đình (Host)' : 'Citadel Trivia (Host)'}
          </h3>
          <span style={{ fontSize: '11px', color: '#888' }}>
            {isVi ? `Mã Phòng: ` : `Room Code: `}<strong>{roomCode}</strong>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          {onMinimize && (
            <button onClick={onMinimize} style={{
              background: 'none', border: 'none', cursor: 'pointer', color: '#0f5f59',
              display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: '700'
            }}>
              <MessageSquare size={16} />
              {isVi ? 'Xem Chat' : 'View Chat'}
            </button>
          )}

          <button onClick={onBack} style={{
            background: 'none', border: 'none', cursor: 'pointer', color: '#666',
            display: 'flex', alignItems: 'center', gap: '4px', fontSize: '13px', fontWeight: '700'
          }}>
            <X size={16} />
            {isVi ? 'Đóng' : 'Close'}
          </button>
        </div>
      </div>

      <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>

        {/* ─── 1. LOBBY STATE ─── */}
        {roomState.status === 'lobby' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px', margin: 'auto 0' }}>
            
            {/* QR Connection Column */}
            <div style={{
              backgroundColor: '#fff', borderRadius: '24px', padding: '24px',
              border: '1px solid #eef2f5', boxShadow: '0 4px 20px rgba(0,0,0,0.02)',
              textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center'
            }}>
              <span style={{ fontSize: '11px', color: '#b2820a', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {isVi ? 'BẠN BÈ QUÉT MÃ ĐỂ VÀO CHƠI' : 'FRIENDS SCAN CODE TO JOIN'}
              </span>
              <h2 style={{ fontSize: '32px', fontWeight: '900', color: '#0f5f59', margin: '8px 0 16px 0', letterSpacing: '2px' }}>
                {roomCode}
              </h2>
              
              {/* QR Image Container */}
              <div style={{
                padding: '12px', border: '2px dashed #0f5f59', borderRadius: '16px',
                backgroundColor: '#f9f9f9', marginBottom: '16px'
              }}>
                <img 
                  src={qrCodeUrl} 
                  alt="QR Code to Join" 
                  style={{ width: '180px', height: '180px', display: 'block' }}
                />
              </div>

              <p style={{ fontSize: '11px', color: '#777', lineHeight: '1.4', margin: '0 0 16px 0' }}>
                {isVi 
                  ? 'Host cần kết nối cùng Wi-Fi nội bộ và chia sẻ trang web để mọi người cùng kết nối.' 
                  : 'Host should share the link or open on local IP so friends can scan and connect.'}
              </p>

              {/* Security/SSL Bypass Guide for Mobile Scanning */}
              <div style={{
                width: '100%',
                padding: '12px',
                borderRadius: '12px',
                backgroundColor: '#fff9e6',
                border: '1.5px solid #ffe0b2',
                textAlign: 'left'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#e65100', fontWeight: '700', fontSize: '11px', marginBottom: '6px' }}>
                  <AlertCircle size={14} />
                  <span>{isVi ? 'HƯỚNG DẪN KHẮC PHỤC CẢNH BÁO BẢO MẬT (SSL)' : 'HOW TO BYPASS SECURITY WARNING (SSL)'}</span>
                </div>
                <p style={{ margin: 0, fontSize: '10.5px', color: '#5d4037', lineHeight: '1.4' }}>
                  {isVi ? (
                    <>
                      Khi quét mã, điện thoại sẽ hiện cảnh báo bảo mật vì ứng dụng sử dụng SSL tự ký. Đừng lo lắng, hãy làm như sau:
                      <br />
                      • <strong>Android / Chrome</strong>: Bấm <strong>&quot;Nâng cao&quot; (Advanced)</strong> → Chọn <strong>&quot;Tiếp tục truy cập... (không an toàn)&quot; (Proceed)</strong>.
                      <br />
                      • <strong>iOS / Safari</strong>: Bấm <strong>&quot;Hiển thị chi tiết&quot; (Show Details)</strong> → Chọn <strong>&quot;Truy cập trang web này&quot; (Visit this website)</strong> → Xác nhận.
                    </>
                  ) : (
                    <>
                      When scanning, your phone will show a security warning because of self-signed SSL. Don&apos;t worry, proceed as follows:
                      <br />
                      • <strong>Android / Chrome</strong>: Tap <strong>&quot;Advanced&quot;</strong> → Tap <strong>&quot;Proceed to ... (unsafe)&quot;</strong>.
                      <br />
                      • <strong>iOS / Safari</strong>: Tap <strong>&quot;Show Details&quot;</strong> → Tap <strong>&quot;Visit this website&quot;</strong> → Confirm.
                    </>
                  )}
                </p>
              </div>
            </div>

            {/* Lobby Players List Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{
                backgroundColor: '#fff', borderRadius: '24px', padding: '20px',
                border: '1px solid #eef2f5', flex: 1, display: 'flex', flexDirection: 'column'
              }}>
                <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '700', color: '#333', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Users size={16} />
                    {isVi ? `Thành viên (${roomState.players.length})` : `Players (${roomState.players.length})`}
                  </h4>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', maxHeight: '200px', display: 'flex', flexWrap: 'wrap', gap: '8px', alignContent: 'flex-start' }}>
                  {roomState.players.length === 0 ? (
                    <div style={{ margin: 'auto', textAlign: 'center', color: '#999', fontSize: '13px' }}>
                      {isVi ? 'Đang đợi mọi người vào phòng...' : 'Waiting for players to join...'}
                    </div>
                  ) : (
                    roomState.players.map((p, idx) => (
                      <div 
                        key={idx} 
                        style={{
                          padding: '8px 14px', borderRadius: '10px',
                          backgroundColor: '#edf5ef', border: '1px solid rgba(15,95,89,0.15)',
                          color: '#0f5f59', fontWeight: '700', fontSize: '13px',
                          display: 'flex', alignItems: 'center', gap: '4px',
                          animation: 'popIn 0.2s ease-out'
                        }}
                      >
                        {p.nickname}
                      </div>
                    ))
                  )}
                </div>
              </div>

              <button
                onClick={handleStart}
                disabled={roomState.players.length === 0 || loading}
                style={{
                  width: '100%', padding: '16px', borderRadius: '14px', border: 'none',
                  background: roomState.players.length > 0 ? 'linear-gradient(135deg, #0f5f59, #164c5e)' : '#ccc',
                  color: 'white', fontWeight: '700', fontSize: '15px',
                  cursor: roomState.players.length > 0 ? 'pointer' : 'not-allowed',
                  boxShadow: roomState.players.length > 0 ? '0 6px 20px rgba(15,95,89,0.3)' : 'none',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px'
                }}
              >
                {loading ? <Loader2 className="spin" size={18} /> : <Play size={18} />}
                {isVi ? 'BẮT ĐẦU TRÒ CHƠI' : 'START THE GAME'}
              </button>
            </div>

          </div>
        )}

        {/* ─── 2. PLAYING STATE (Host Question Screen) ─── */}
        {roomState.status === 'playing' && roomState.current_question && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px' }}>
            
            {/* Question Text block */}
            <div style={{
              backgroundColor: '#fff', borderRadius: '24px', padding: '24px',
              border: '1px solid #eef2f5', textAlign: 'center',
              boxShadow: '0 4px 15px rgba(0,0,0,0.02)'
            }}>
              <span style={{ fontSize: '11px', color: '#b2820a', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                {isVi ? `CÂU HỎI ${roomState.current_question.question_index + 1} / ${roomState.total_questions}` : `QUESTION ${roomState.current_question.question_index + 1} / ${roomState.total_questions}`}
              </span>
              <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#333', marginTop: '10px', lineHeight: '1.4' }}>
                {roomState.current_question.question_text}
              </h2>
            </div>

            {/* Answer Options list (Non-revealed) */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              {roomState.current_question.options.map((opt, idx) => (
                <div 
                  key={idx}
                  style={{
                    padding: '20px', borderRadius: '16px', background: optionStyles[idx].bg,
                    color: 'white', display: 'flex', alignItems: 'center', gap: '14px',
                    boxShadow: '0 4px 10px rgba(0,0,0,0.08)'
                  }}
                >
                  <span style={{ fontSize: '24px', fontWeight: '900' }}>{optionStyles[idx].shape}</span>
                  <span style={{ fontSize: '15px', fontWeight: '600' }}>{opt}</span>
                </div>
              ))}
            </div>

            {/* Timer and submission count info */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              marginTop: 'auto', borderTop: '1px solid #e0e0e0', paddingTop: '16px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '13px', color: '#555', fontWeight: '600' }}>
                  {isVi ? 'Đã nộp bài:' : 'Submitted:'}
                </span>
                <span style={{
                  padding: '4px 10px', borderRadius: '8px', backgroundColor: '#e2f0d9',
                  color: '#385723', fontWeight: '700', fontSize: '12px'
                }}>
                  {roomState.players.reduce((acc, p) => acc + (p.answers_count > roomState.current_question.question_index ? 1 : 0), 0)} / {roomState.players.length}
                </span>
              </div>

              <button
                onClick={handleNext}
                disabled={loading}
                style={{
                  padding: '12px 24px', borderRadius: '10px', border: 'none',
                  background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
                  color: '#fff', fontWeight: '700', fontSize: '14px',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px',
                  boxShadow: '0 4px 12px rgba(15,95,89,0.2)'
                }}
              >
                {isVi ? 'Xem Đáp Án' : 'Show Answer'}
                <ChevronRight size={16} />
              </button>
            </div>

          </div>
        )}

        {/* ─── 3. SCOREBOARD STATE (Correct answers reveal + current scoreboard) ─── */}
        {roomState.status === 'scoreboard' && roomState.current_question && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px', height: '100%' }}>
            
            {/* Answer Reveal Left Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{
                backgroundColor: '#fff', borderRadius: '24px', padding: '20px',
                border: '1px solid #eef2f5', boxShadow: '0 4px 10px rgba(0,0,0,0.02)'
              }}>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '16px', color: '#2e7d32', fontWeight: '800' }}>
                  {isVi ? '✓ Đáp án đúng' : '✓ Correct Answer'}
                </h3>
                
                <div style={{
                  padding: '14px 20px', borderRadius: '12px',
                  background: optionStyles[roomState.current_question.correct_option_index].bg,
                  color: 'white', display: 'flex', alignItems: 'center', gap: '12px',
                  fontWeight: '700', fontSize: '14px'
                }}>
                  <span>{optionStyles[roomState.current_question.correct_option_index].shape}</span>
                  <span>{roomState.current_question.options[roomState.current_question.correct_option_index]}</span>
                </div>
              </div>

              {/* AI Explanation note */}
              {roomState.current_question.explanation && (
                <div style={{
                  backgroundColor: '#edf7ed', border: '1px solid #c3e6cb',
                  borderRadius: '24px', padding: '20px', flex: 1
                }}>
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', fontWeight: '700', color: '#1e4620', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={16} />
                    {isVi ? 'Bên lề lịch sử' : 'Historical Insight'}
                  </h4>
                  <p style={{ margin: 0, fontSize: '13px', color: '#2b542c', lineHeight: '1.5' }}>
                    {roomState.current_question.explanation}
                  </p>
                </div>
              )}
            </div>

            {/* Scoreboard Right Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{
                backgroundColor: '#fff', borderRadius: '24px', padding: '20px',
                border: '1px solid #eef2f5', flex: 1, display: 'flex', flexDirection: 'column'
              }}>
                <h4 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '700', color: '#333', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Trophy size={16} color="#b2820a" />
                  {isVi ? 'Bảng Điểm Hiện Tại' : 'Current Standings'}
                </h4>

                <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {roomState.players.map((p, idx) => (
                    <div 
                      key={idx} 
                      style={{
                        padding: '10px 14px', borderRadius: '10px',
                        backgroundColor: idx === 0 ? '#fff8e1' : '#f8f9fa',
                        border: idx === 0 ? '1.5px solid #ffe082' : '1px solid #eee',
                        display: 'flex', justifyItems: 'center', justifyContent: 'space-between', alignItems: 'center'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <span style={{
                          fontSize: '12px', fontWeight: '800', width: '22px', height: '22px',
                          borderRadius: '50%', backgroundColor: idx === 0 ? '#ffb300' : '#ddd',
                          color: 'white', display: 'grid', placeItems: 'center'
                        }}>
                          {idx + 1}
                        </span>
                        <strong style={{ fontSize: '13px', color: '#333' }}>{p.nickname}</strong>
                      </div>
                      <span style={{ fontSize: '13px', fontWeight: '700', color: '#555' }}>
                        {p.score} pts
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <button
                onClick={handleNext}
                disabled={loading}
                style={{
                  width: '100%', padding: '16px', borderRadius: '14px', border: 'none',
                  background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
                  color: 'white', fontWeight: '700', fontSize: '14px',
                  cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px',
                  boxShadow: '0 4px 15px rgba(15,95,89,0.2)'
                }}
              >
                {isVi ? 'Đi tiếp' : 'Continue'}
                <ChevronRight size={16} />
              </button>
            </div>

          </div>
        )}

        {/* ─── 4. FINISHED STATE (Podium + AI Speech Card) ─── */}
        {roomState.status === 'finished' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '24px', height: '100%', margin: 'auto 0' }}>
            
            {/* Podium Left Column */}
            <div style={{
              backgroundColor: '#fff', borderRadius: '24px', padding: '24px',
              border: '1px solid #eef2f5', boxShadow: '0 4px 20px rgba(0,0,0,0.02)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
            }}>
              <div style={{
                width: '60px', height: '60px', borderRadius: '50%',
                backgroundColor: '#fff8e1', color: '#ffb300',
                display: 'grid', placeItems: 'center', marginBottom: '12px',
                boxShadow: '0 4px 12px rgba(255,179,0,0.15)'
              }}>
                <Trophy size={32} />
              </div>
              
              <span style={{ fontSize: '11px', color: '#b2820a', fontWeight: '700', textTransform: 'uppercase' }}>
                {isVi ? 'QUÁN QUÂN' : 'WINNER'}
              </span>
              
              {roomState.players[0] ? (
                <>
                  <h2 style={{ fontSize: '26px', fontWeight: '900', color: '#0f5f59', margin: '6px 0' }}>
                    {roomState.players[0].nickname}
                  </h2>
                  <div style={{
                    padding: '6px 14px', borderRadius: '10px', backgroundColor: '#fff8e1',
                    fontSize: '13px', fontWeight: '700', color: '#ffb300'
                  }}>
                    {roomState.players[0].score} pts
                  </div>
                </>
              ) : (
                <span style={{ fontSize: '13px', color: '#666' }}>-</span>
              )}

              {/* Show second and third place list */}
              {roomState.players.length > 1 && (
                <div style={{ width: '100%', borderTop: '1px solid #eee', marginTop: '20px', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {roomState.players.slice(1, 3).map((p, i) => (
                    <div key={i} style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
                      <span style={{ color: '#666', fontWeight: '500' }}>
                        {i === 0 ? '🥈 hạng 2:' : '🥉 hạng 3:'} <strong>{p.nickname}</strong>
                      </span>
                      <span style={{ fontWeight: '700', color: '#888' }}>{p.score} pts</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* AI Victory Praise Speech Right Column */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{
                backgroundColor: 'rgba(255, 255, 255, 0.7)', backdropFilter: 'blur(10px)',
                borderRadius: '24px', padding: '24px', border: '1px solid rgba(15,95,89,0.2)',
                boxShadow: '0 8px 32px rgba(15, 95, 89, 0.08)', flex: 1,
                display: 'flex', flexDirection: 'column'
              }}>
                <div style={{ display: 'flex', justifyItems: 'center', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                  <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '800', color: '#0f5f59', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Sparkles size={16} />
                    {isVi ? 'Tổng kết từ AI của Vua' : 'AI Coronation Address'}
                  </h4>
                  {praiseText && (
                    <button 
                      onClick={handleSpeakPraise}
                      style={{
                        background: 'none', border: 'none', cursor: 'pointer', color: '#0f5f59',
                        padding: '4px', display: 'grid', placeItems: 'center'
                      }}
                      title={isVi ? 'Đọc lại' : 'Replay Audio'}
                    >
                      <Volume2 size={16} />
                    </button>
                  )}
                </div>

                <div style={{ flex: 1, overflowY: 'auto', maxHeight: '180px' }}>
                  {loadingPraise ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '8px' }}>
                      <Loader2 className="spin" size={24} color="#0f5f59" />
                      <span style={{ fontSize: '11px', color: '#999' }}>{isVi ? 'Đang soạn thánh chỉ...' : 'Drafting speech...'}</span>
                    </div>
                  ) : (
                    <p style={{
                      margin: 0, fontSize: '13px', color: '#333', lineHeight: '1.6',
                      fontStyle: 'italic', whiteSpace: 'pre-wrap'
                    }}>
                      {praiseText || (isVi ? 'Đang tải lời khen ngợi từ Hoàng cung...' : 'Loading congratulations address...')}
                    </p>
                  )}
                </div>
              </div>

              <button
                onClick={onBack}
                style={{
                  width: '100%', padding: '16px', borderRadius: '14px', border: 'none',
                  background: 'linear-gradient(135deg, #0f5f59, #164c5e)',
                  color: 'white', fontWeight: '700', fontSize: '14px',
                  cursor: 'pointer', boxShadow: '0 4px 15px rgba(15,95,89,0.2)'
                }}
              >
                {isVi ? 'Hoàn thành đấu trí' : 'Finish Trivia'}
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
};

export default GameHost;

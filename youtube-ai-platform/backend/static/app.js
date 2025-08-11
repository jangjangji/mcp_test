const API_BASE_URL = 'http://localhost:8080';

// 유사도 검색
async function searchSimilar() {
    const query = document.getElementById('searchQuery').value.trim();
    if (!query) {
        alert('검색어를 입력해주세요.');
        return;
    }

    showLoading('searchLoading');
    hideResult('searchResult');

    try {
        const response = await fetch(`${API_BASE_URL}/api/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });

        const result = await response.json();
        displaySearchResult(result);
    } catch (error) {
        console.error('Error:', error);
        displayError('searchResult', '검색 중 오류가 발생했습니다.');
    } finally {
        hideLoading('searchLoading');
    }
}

// YouTube 검색
async function searchYouTube() {
    const query = document.getElementById('search-input').value;
    if (!query) {
        showAlert('search-result', '검색어를 입력해주세요.', 'warning');
        return;
    }

    showLoading('search-result');
    try {
        const response = await fetch('http://localhost:3000/api/youtube/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });

        const result = await response.json();
        console.log('검색 결과:', result);

        if (result.success && result.data) {
            displaySearchResults(result.data);
        } else {
            showAlert('search-result', `검색 실패: ${result.error || '알 수 없는 오류'}`, 'danger');
        }
    } catch (error) {
        console.error('API 오류:', error);
        showAlert('search-result', `API 호출 중 오류: ${error.message}`, 'danger');
    }
}

// 채널 정보 가져오기
async function getChannelInfo() {
    const videoUrl = document.getElementById('channelVideoUrl').value.trim();
    if (!videoUrl) {
        alert('YouTube 영상 URL을 입력해주세요.');
        return;
    }

    showLoading('channelLoading');
    hideResult('channelResult');

    try {
        const response = await fetch(`${API_BASE_URL}/api/channel/info`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ video_url: videoUrl })
        });

        const channelInfo = await response.json();
        displayChannelInfo(channelInfo);
    } catch (error) {
        console.error('Error:', error);
        displayError('channelResult', '채널 정보 가져오기 중 오류가 발생했습니다.');
    } finally {
        hideLoading('channelLoading');
    }
}

// 자막 가져오기
async function getTranscript() {
    const url = document.getElementById('transcriptUrl').value.trim();
    if (!url) {
        alert('YouTube 영상 URL을 입력해주세요.');
        return;
    }

    showLoading('transcriptLoading');
    hideResult('transcriptResult');

    try {
        const response = await fetch(`${API_BASE_URL}/api/transcript`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        const result = await response.json();
        displayTranscriptResult(result);
    } catch (error) {
        console.error('Error:', error);
        displayError('transcriptResult', '자막 가져오기 중 오류가 발생했습니다.');
    } finally {
        hideLoading('transcriptLoading');
    }
}

// 채널 저장
async function saveChannel() {
    const channelId = document.getElementById('saveChannelId').value.trim();
    if (!channelId) {
        alert('채널 ID를 입력해주세요.');
        return;
    }

    showLoading('saveChannelLoading');
    hideResult('saveChannelResult');

    try {
        const response = await fetch(`${API_BASE_URL}/api/channel/save`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ channel_id: channelId })
        });

        const result = await response.json();
        displaySaveChannelResult(result);
    } catch (error) {
        console.error('Error:', error);
        displayError('saveChannelResult', '채널 저장 중 오류가 발생했습니다.');
    } finally {
        hideLoading('saveChannelLoading');
    }
}

// 단일 영상 저장 미리보기
async function previewTranscript() {
    const videoUrl = document.getElementById('single-video-url').value.trim();
    if (!videoUrl) {
        alert('YouTube 영상 URL을 입력해주세요.');
        return;
    }

    showLoading('preview-result');
    hideResult('preview-result');

    try {
        const response = await fetch(`${API_BASE_URL}/api/transcript`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: videoUrl })
        });

        const result = await response.json();
        console.log('자막 미리보기 결과:', result);
        
        hideLoading('preview-result'); // 로딩 상태 제거
        
        displayPreviewResult(result);
    } catch (error) {
        console.error('Error:', error);
        hideLoading('preview-result'); // 에러 시에도 로딩 상태 제거
        displayError('preview-result', '자막 미리보기 중 오류가 발생했습니다.');
        document.getElementById('save-section').style.display = 'none';
    }
}

// 자막 미리보기 결과 표시
function displayPreviewResult(result) {
    const container = document.getElementById('preview-result');
    
    console.log('displayPreviewResult 호출됨:', result); // 디버깅용
    
    if (result.success && result.data) {
        const data = result.data;
        const transcript = data.transcript || '';
        
        console.log('자막 내용:', transcript); // 디버깅용
        
        // 자막이 없는 경우 체크
        if (!transcript || transcript.includes('자막 추출 실패') || transcript.includes('자막을 찾을 수 없')) {
            container.innerHTML = `
                <div class="alert alert-warning fade-in">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>자막이 없습니다!</strong><br>
                    이 영상에는 자막이 없거나 자막 추출이 불가능합니다.<br>
                    다른 영상을 시도해보세요.
                </div>
            `;
            document.getElementById('save-section').style.display = 'none';
            return;
        }
        
        // 청크 정보 계산 (고급 청킹 전략 사용)
        const chunks = [];
        const chunkSize = 500;
        for (let i = 0; i < transcript.length; i += chunkSize) {
            const chunk = transcript.slice(i, i + chunkSize);
            chunks.push({
                chunk_index: chunks.length,
                chunk_text: chunk,
                chunk_length: chunk.length
            });
        }
        
        let html = `
            <div class="result-container fade-in">
                <h4><i class="fas fa-eye me-2"></i>자막 미리보기</h4>
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>자막 추출 성공!</strong><br>
                    전체 자막 길이: ${transcript.length}자<br>
                    청크 개수: ${chunks.length}개<br>
                    <small><i class="fas fa-info-circle me-1"></i>고급 청킹 전략 사용 (요리 관련 콘텐츠에 특화)</small>
                </div>
                
                <h5><i class="fas fa-align-left me-2"></i>자막 내용 미리보기</h5>
                <div class="transcript-content">
                    <pre style="white-space: pre-wrap; word-wrap: break-word; max-height: 300px; overflow-y: auto;">${transcript.substring(0, 500)}${transcript.length > 500 ? '...' : ''}</pre>
                </div>
                
                <h5 class="mt-3"><i class="fas fa-list me-2"></i>청크 정보</h5>
                <div class="row">
        `;
        
        chunks.forEach((chunk, index) => {
            html += `
                <div class="col-md-6 mb-2">
                    <div class="card">
                        <div class="card-header">
                            <small>청크 ${chunk.chunk_index + 1} (${chunk.chunk_length}자)</small>
                        </div>
                        <div class="card-body">
                            <small style="color: #666;">${chunk.chunk_text.substring(0, 100)}${chunk.chunk_text.length > 100 ? '...' : ''}</small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        document.getElementById('save-section').style.display = 'block'; // 저장 섹션 표시
    } else {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>오류!</strong> ${result.error || '자막 미리보기에 실패했습니다.'}
            </div>
        `;
        document.getElementById('save-section').style.display = 'none';
    }
}

// 단일 영상 저장 (임베딩 저장)
async function saveSingleVideo() {
    const videoUrl = document.getElementById('single-video-url').value.trim();
    if (!videoUrl) {
        alert('YouTube 영상 URL을 입력해주세요.');
        return;
    }

    showLoading('single-video-result');
    hideResult('single-video-result');

    try {
        const response = await fetch(`${API_BASE_URL}/api/save-single-video`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ video_url: videoUrl })
        });

        const result = await response.json();
        displaySingleVideoResult(result);
    } catch (error) {
        console.error('Error:', error);
        displayError('single-video-result', '단일 영상 저장 중 오류가 발생했습니다.');
    } finally {
        hideLoading('single-video-result');
    }
}

// 단일 영상 저장 결과 표시
function displaySingleVideoResult(result) {
    const container = document.getElementById('single-video-result');
    
    if (result.success) {
        let message = result.data?.message || '단일 영상 저장이 완료되었습니다.';
        
        container.innerHTML = `
            <div class="alert alert-success" role="alert">
                <i class="fas fa-check-circle"></i>
                <strong>성공!</strong> ${message}
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle"></i>
                <strong>오류!</strong> ${result.error || '알 수 없는 오류가 발생했습니다.'}
            </div>
        `;
    }
}

// 검색 결과 표시
function displaySearchResult(result) {
    const container = document.getElementById('searchResult');
    
    if (result.error) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle"></i>
                ${result.error}
            </div>
        `;
        return;
    }

    if (!result.video_id) {
        container.innerHTML = `
            <div class="alert alert-info" role="alert">
                <i class="fas fa-info-circle"></i>
                유사한 비디오를 찾을 수 없습니다.
            </div>
        `;
        return;
    }

    const score = result.score ? (result.score * 100).toFixed(1) : 'N/A';
    
    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-video"></i> 유사한 비디오</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-8">
                        <h6>비디오 정보</h6>
                        <p><strong>비디오 ID:</strong> ${result.video_id}</p>
                        <p><strong>URL:</strong> <a href="${result.url}" target="_blank">${result.url}</a></p>
                        <p><strong>청크 인덱스:</strong> ${result.chunk_index || 'N/A'}</p>
                        <p><strong>유사도 점수:</strong> ${score}%</p>
                    </div>
                    <div class="col-md-4">
                        <h6>자막 청크</h6>
                        <div class="border p-3 bg-light">
                            <p class="mb-0">${result.chunk_text || '자막 내용이 없습니다.'}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// YouTube 검색 결과 표시
function displayYouTubeSearchResult(videos) {
    const container = document.getElementById('youtubeSearchResult');
    
    if (!Array.isArray(videos) || videos.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info" role="alert">
                <i class="fas fa-info-circle"></i>
                검색 결과가 없습니다.
            </div>
        `;
        return;
    }

    const videoCards = videos.map(video => `
        <div class="col-md-6 col-lg-4 mb-4">
            <div class="card video-card h-100">
                <img src="${video.thumbnail}" class="card-img-top thumbnail" alt="${video.title}">
                <div class="card-body">
                    <h6 class="card-title">${video.title}</h6>
                    <p class="card-text text-muted">${video.channel}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="fas fa-eye"></i> ${video.views}
                        </small>
                        <small class="text-muted">
                            <i class="fas fa-thumbs-up"></i> ${video.likes}
                        </small>
                    </div>
                </div>
                <div class="card-footer">
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="fas fa-clock"></i> ${video.duration}
                        </small>
                        <small class="text-muted">
                            <i class="fas fa-calendar"></i> ${video.published}
                        </small>
                    </div>
                    <div class="mt-2">
                        <span class="badge bg-primary">${video.video_id}</span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="row">
            ${videoCards}
        </div>
    `;
}

// 채널 정보 표시
function displayChannelInfo(channelInfo) {
    const container = document.getElementById('channelResult');
    
    if (channelInfo.error) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle"></i>
                ${channelInfo.error}
            </div>
        `;
        return;
    }

    const recentVideos = channelInfo.recent_videos ? channelInfo.recent_videos.map(video => `
        <div class="col-md-6 mb-3">
            <div class="card">
                <div class="row g-0">
                    <div class="col-md-4">
                        <img src="${video.thumbnail_url}" class="img-fluid rounded-start" alt="${video.title}">
                    </div>
                    <div class="col-md-8">
                        <div class="card-body">
                            <h6 class="card-title">${video.title}</h6>
                            <p class="card-text">
                                <small class="text-muted">
                                    <i class="fas fa-eye"></i> ${formatNumber(video.view_count)} |
                                    <i class="fas fa-thumbs-up"></i> ${formatNumber(video.like_count)}
                                </small>
                            </p>
                            <a href="${video.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                <i class="fab fa-youtube"></i> 보기
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `).join('') : '';

    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-tv"></i> 채널 정보</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>채널 정보</h6>
                        <p><strong>채널 ID:</strong> ${channelInfo.channel_id}</p>
                        <p><strong>채널명:</strong> ${channelInfo.channel_name}</p>
                    </div>
                </div>
                <hr>
                <h6>최근 영상들</h6>
                <div class="row">
                    ${recentVideos}
                </div>
            </div>
        </div>
    `;
}

// 자막 결과 표시
function displayTranscriptResult(data) {
    const container = document.getElementById('transcript-result');
    
    // 오류 체크 개선
    if (data.error || (data.transcript && (data.transcript.includes('자막 추출 실패') || data.transcript.includes('자막을 찾을 수 없')))) {
        const errorMsg = data.error || data.transcript || '자막 추출에 실패했습니다.';
        
        // 자막이 없는 경우 특별한 메시지 표시
        if (data.transcript && (data.transcript.includes('자막 추출 실패') || data.transcript.includes('자막을 찾을 수 없'))) {
            container.innerHTML = `
                <div class="alert alert-warning fade-in">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>자막이 없습니다!</strong><br>
                    이 영상에는 자막이 없거나 자막 추출이 불가능합니다.<br>
                    다른 영상을 시도해보세요.
                </div>
            `;
        } else {
            showAlert('transcript-result', errorMsg, 'warning');
        }
        return;
    }

    // video_id 추출 (URL에서)
    const url = document.getElementById('transcript-url').value;
    const videoIdMatch = url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
    const videoId = videoIdMatch ? videoIdMatch[1] : 'unknown';

    const html = `
        <div class="result-container fade-in">
            <h4><i class="fas fa-closed-captioning me-2"></i>자막 내용</h4>
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i>
                <strong>자막 추출 성공!</strong>
            </div>
            <div class="video-item">
                <img src="https://img.youtube.com/vi/${videoId}/mqdefault.jpg" 
                     class="video-thumbnail" 
                     alt="썸네일" 
                     onerror="this.onerror=null; this.src='https://img.youtube.com/vi/${videoId}/hqdefault.jpg';"
                     onload="console.log('자막 추출 영상 썸네일 로딩 성공:', this.src)">
                <div class="video-info">
                    <div class="video-title">${data.title || '제목 없음'}</div>
                    <div class="video-meta">
                        <i class="fas fa-clock me-2"></i>길이: ${data.duration || 'N/A'}<br>
                        <i class="fas fa-file-text me-2"></i>자막 길이: ${data.transcript ? data.transcript.length : 0}자
                    </div>
                </div>
            </div>
            
            <div class="mt-4">
                <h5><i class="fas fa-align-left me-2"></i>전체 자막</h5>
                <div class="transcript-content">
                    <pre style="white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto;">${data.transcript || '자막을 찾을 수 없습니다.'}</pre>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

// 채널 저장 결과 표시
function displaySaveChannelResult(result) {
    const container = document.getElementById('saveChannelResult');
    
    if (result.error) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle"></i>
                ${result.error}
            </div>
        `;
        return;
    }

    // 결과 메시지를 줄바꿈으로 분리하여 각 단계별로 표시
    const steps = result.message.split('\n').filter(step => step.trim() !== '');
    
    let stepsHtml = '';
    steps.forEach(step => {
        let icon = '📋';
        let alertClass = 'alert-info';
        
        if (step.includes('✅')) {
            icon = '✅';
            alertClass = 'alert-success';
        } else if (step.includes('❌')) {
            icon = '❌';
            alertClass = 'alert-danger';
        } else if (step.includes('⚠️')) {
            icon = '⚠️';
            alertClass = 'alert-warning';
        } else if (step.includes('📝')) {
            icon = '📝';
            alertClass = 'alert-info';
        } else if (step.includes('💾')) {
            icon = '💾';
            alertClass = 'alert-success';
        } else if (step.includes('📊')) {
            icon = '📊';
            alertClass = 'alert-primary';
        }
        
        stepsHtml += `
            <div class="alert ${alertClass} mb-2" role="alert">
                <i class="fas fa-info-circle"></i>
                ${step}
            </div>
        `;
    });

    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-save"></i> 채널 저장 진행 상황</h5>
            </div>
            <div class="card-body">
                ${stepsHtml}
            </div>
        </div>
    `;
}

// 유틸리티 함수들
function showAlert(elementId, message, type = 'info') {
    const container = document.getElementById(elementId);
    container.innerHTML = `
        <div class="alert alert-${type}" role="alert">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
        </div>
    `;
}

function showLoading(elementId) {
    const container = document.getElementById(elementId);
    container.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">로딩 중...</span>
            </div>
            <p class="mt-2">처리 중입니다...</p>
        </div>
    `;
}

function hideLoading(elementId) {
    const container = document.getElementById(elementId);
    container.innerHTML = '';
}

function hideResult(elementId) {
    document.getElementById(elementId).innerHTML = '';
}

function displayError(elementId, message) {
    document.getElementById(elementId).innerHTML = `
        <div class="alert alert-danger" role="alert">
            <i class="fas fa-exclamation-triangle"></i>
            ${message}
        </div>
    `;
}

function formatNumber(num) {
    if (!num) return '0';
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Enter 키 이벤트 처리
document.addEventListener('DOMContentLoaded', function() {
    // 실제 HTML에 존재하는 요소들만 이벤트 리스너 추가
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') searchYouTube();
        });
    }
    
    const channelUrl = document.getElementById('channel-url');
    if (channelUrl) {
        channelUrl.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') analyzeChannel();
        });
    }
    
    const transcriptUrl = document.getElementById('transcript-url');
    if (transcriptUrl) {
        transcriptUrl.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') extractTranscript();
        });
    }
    
    const singleVideoUrl = document.getElementById('single-video-url');
    if (singleVideoUrl) {
        singleVideoUrl.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') saveSingleVideo();
        });
    }
    
    const similarityQuery = document.getElementById('similarity-query');
    if (similarityQuery) {
        similarityQuery.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') searchSimilar();
        });
    }
    
    const videoSearchQuery = document.getElementById('video-search-query');
    if (videoSearchQuery) {
        videoSearchQuery.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') searchVideo();
        });
    }
});

// 의미 기반 청킹 저장
async function saveSemanticVideo() {
    const videoUrl = document.getElementById('semantic-video-url').value.trim();
    if (!videoUrl) {
        alert('YouTube 영상 URL을 입력해주세요.');
        return;
    }
    
    const chunkMethod = document.querySelector('input[name="chunkMethod"]:checked').value;
    
    showLoading('semantic-result');
    hideResult('semantic-result');

    try {
        const response = await fetch(`${API_BASE_URL}/api/save-single-video-semantic`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                video_url: videoUrl,
                chunk_method: chunkMethod
            })
        });

        const result = await response.json();
        displaySemanticResult(result, chunkMethod);
    } catch (error) {
        console.error('Error:', error);
        displayError('semantic-result', '의미 기반 청킹 저장 중 오류가 발생했습니다.');
    } finally {
        hideLoading('semantic-result');
    }
}

// 의미 기반 청킹 결과 표시
function displaySemanticResult(result, chunkMethod) {
    const container = document.getElementById('semantic-result');
    
    if (result.success) {
        const methodNames = {
            'basic': '기본 청킹',
            'semantic': '의미 기반 청킹',
            'cooking': '요리 특화 청킹'
        };
        
        container.innerHTML = `
            <div class="alert alert-success" role="alert">
                <i class="fas fa-check-circle me-2"></i>
                <strong>저장 완료!</strong><br>
                청킹 방법: ${methodNames[chunkMethod] || chunkMethod}<br>
                결과: ${result.data?.message || result.data}
            </div>
        `;
    } else {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>오류!</strong> ${result.error || '의미 기반 청킹 저장에 실패했습니다.'}
            </div>
        `;
    }
}

// 청킹 방법 비교
async function compareChunking() {
    const videoUrl = document.getElementById('compare-video-url').value.trim();
    if (!videoUrl) {
        alert('YouTube 영상 URL을 입력해주세요.');
        return;
    }
    
    showLoading('compare-result');
    hideResult('compare-result');

    try {
        const response = await fetch(`${API_BASE_URL}/api/compare-chunking`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ video_url: videoUrl })
        });

        const result = await response.json();
        displayCompareResult(result);
    } catch (error) {
        console.error('Error:', error);
        displayError('compare-result', '청킹 방법 비교 중 오류가 발생했습니다.');
    } finally {
        hideLoading('compare-result');
    }
}

// 청킹 방법 비교 결과 표시
function displayCompareResult(result) {
    const container = document.getElementById('compare-result');
    
    if (result.success && result.data) {
        const data = result.data;
        
        let html = `
            <div class="card">
                <div class="card-header">
                    <h5><i class="fas fa-chart-bar me-2"></i>청킹 방법 비교 결과</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header">
                                    <h6><i class="fas fa-list me-2"></i>기본 청킹</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>청크 개수:</strong> ${data.basic_chunking?.chunk_count || 0}개</p>
                                    <p><strong>평균 길이:</strong> ${Math.round(data.basic_chunking?.avg_chunk_length || 0)}자</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header">
                                    <h6><i class="fas fa-brain me-2"></i>의미 기반 청킹</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>청크 개수:</strong> ${data.semantic_chunking?.chunk_count || 0}개</p>
                                    <p><strong>평균 길이:</strong> ${Math.round(data.semantic_chunking?.avg_chunk_length || 0)}자</p>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="card">
                                <div class="card-header">
                                    <h6><i class="fas fa-utensils me-2"></i>요리 특화 청킹</h6>
                                </div>
                                <div class="card-body">
                                    <p><strong>청크 개수:</strong> ${data.cooking_semantic_chunking?.chunk_count || 0}개</p>
                                    <p><strong>평균 길이:</strong> ${Math.round(data.cooking_semantic_chunking?.avg_chunk_length || 0)}자</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-3">
                        <h6><i class="fas fa-info-circle me-2"></i>샘플 청크</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <h6>기본 청킹 샘플:</h6>
                                <div class="alert alert-light">
                                    <small>${data.basic_chunking?.sample_chunks?.[0]?.substring(0, 100) || '샘플 없음'}...</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <h6>의미 기반 청킹 샘플:</h6>
                                <div class="alert alert-light">
                                    <small>${data.semantic_chunking?.sample_chunks?.[0]?.substring(0, 100) || '샘플 없음'}...</small>
                                </div>
                            </div>
                            <div class="col-md-4">
                                <h6>요리 특화 청킹 샘플:</h6>
                                <div class="alert alert-light">
                                    <small>${data.cooking_semantic_chunking?.sample_chunks?.[0]?.substring(0, 100) || '샘플 없음'}...</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    } else {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>오류!</strong> ${result.error || '청킹 방법 비교에 실패했습니다.'}
            </div>
        `;
    }
} 

// 비디오 업로드 함수
async function uploadVideo() {
    const fileInput = document.getElementById('video-file');
    const videoIdInput = document.getElementById('video-id');
    const resultDiv = document.getElementById('video-upload-result');
    
    if (!fileInput.files[0]) {
        showAlert('video-upload-result', '비디오 파일을 선택해주세요.', 'warning');
        return;
    }
    
    const file = fileInput.files[0];
    const videoId = videoIdInput.value || file.name.replace(/\.[^/.]+$/, "");
    
    showLoading('video-upload-result');
    
    try {
        // 파일을 서버로 업로드
        const formData = new FormData();
        formData.append('video', file);
        formData.append('video_id', videoId);
        formData.append('original_filename', file.name); // 원본 파일명 추가
        
        const response = await fetch('/api/upload-video', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success" role="alert">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>성공!</strong> 비디오가 성공적으로 업로드되었습니다.
                    <br><small>비디오 ID: ${videoId}</small>
                </div>
            `;
        } else {
            showAlert('video-upload-result', `업로드 실패: ${result.error}`, 'danger');
        }
    } catch (error) {
        console.error('업로드 오류:', error);
        showAlert('video-upload-result', `업로드 중 오류가 발생했습니다: ${error.message}`, 'danger');
    }
}

// 비디오 검색 함수
async function searchVideo() {
    const query = document.getElementById('video-search-query').value.trim();
    const topK = parseInt(document.getElementById('video-search-top-k').value) || 5;
    
    if (!query) {
        showAlert('video-search-result', '검색어를 입력해주세요.', 'warning');
        return;
    }
    
    showLoading('video-search-result');
    
    try {
        const response = await fetch('/api/search-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: query,
                top_k: topK
            })
        });
        
        const result = await response.json();
        console.log('백엔드 응답:', result); // 디버깅 로그 추가
        
        if (result.success && result.data) {
            // 백엔드에서 반환하는 데이터 구조 처리
            let searchResults;
            console.log('result.data:', result.data); // 디버깅 로그 추가
            
            if (result.data.message) {
                // message 필드 안의 JSON 문자열을 파싱
                console.log('message 필드 발견:', result.data.message); // 디버깅 로그 추가
                try {
                    searchResults = JSON.parse(result.data.message);
                    console.log('파싱된 결과:', searchResults); // 디버깅 로그 추가
                } catch (e) {
                    console.error('JSON 파싱 오류:', e);
                    showAlert('video-search-result', '검색 결과 파싱 중 오류가 발생했습니다.', 'danger');
                    return;
                }
            } else if (Array.isArray(result.data)) {
                // 직접 배열인 경우
                searchResults = result.data;
                console.log('직접 배열:', searchResults); // 디버깅 로그 추가
            } else {
                // 다른 경우
                searchResults = result.data;
                console.log('기타 경우:', searchResults); // 디버깅 로그 추가
            }
            
            console.log('최종 검색 결과:', searchResults); // 디버깅 로그 추가
            displayVideoSearchResult(searchResults, query);
        } else {
            showAlert('video-search-result', `검색 실패: ${result.error || '알 수 없는 오류'}`, 'danger');
        }
    } catch (error) {
        console.error('검색 오류:', error);
        showAlert('video-search-result', `검색 중 오류가 발생했습니다: ${error.message}`, 'danger');
    }
}

// 비디오 검색 결과 표시
function displayVideoSearchResult(results, query) {
    const container = document.getElementById('video-search-result');
    
    // results가 배열이 아닌 경우 처리
    if (!results || !Array.isArray(results)) {
        if (results && typeof results === 'object' && results.error) {
            container.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>검색 오류!</strong> ${results.error}
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="alert alert-info" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    <strong>검색 결과 없음</strong> "${query}"에 대한 검색 결과가 없습니다.
                </div>
            `;
        }
        return;
    }
    
    if (results.length === 0) {
        container.innerHTML = `
            <div class="alert alert-info" role="alert">
                <i class="fas fa-info-circle me-2"></i>
                <strong>검색 결과 없음</strong> "${query}"에 대한 검색 결과가 없습니다.
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-search me-2"></i>검색 결과: "${query}"</h5>
                <small>총 ${results.length}개 결과</small>
            </div>
            <div class="card-body">
    `;
    
    results.forEach((result, index) => {
        const timestamp = formatTimestamp(result.timestamp);
        const similarity = (result.similarity * 100).toFixed(1);
        
        html += `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <h6 class="card-title">
                                <i class="fas fa-video me-2"></i>${result.video_id}
                            </h6>
                            <p class="card-text">
                                <strong>시간:</strong> ${timestamp}<br>
                                <strong>파일:</strong> ${result.video_path}
                            </p>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="badge bg-success fs-6">
                                유사도: ${similarity}%
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// 시간 포맷팅 함수 (초 -> HH:MM:SS)
function formatTimestamp(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
} 

// 유틸리티 함수들
function showAlert(elementId, message, type = 'info') {
    const container = document.getElementById(elementId);
    container.innerHTML = `
        <div class="alert alert-${type}" role="alert">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'danger' ? 'exclamation-triangle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
            ${message}
        </div>
    `;
}

function showLoading(elementId) {
    const container = document.getElementById(elementId);
    container.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">로딩 중...</span>
            </div>
            <p class="mt-2">처리 중입니다...</p>
        </div>
    `;
}

function hideLoading(elementId) {
    const container = document.getElementById(elementId);
    container.innerHTML = '';
}

// YouTube 검색
async function searchYouTube() {
    const query = document.getElementById('search-input').value;
    if (!query) {
        showAlert('search-result', '검색어를 입력해주세요.', 'warning');
        return;
    }

    showLoading('search-result');
    try {
        const response = await fetch('/api/search-youtube', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });

        const result = await response.json();
        console.log('검색 결과:', result);

        if (result.success && result.data) {
            displaySearchResults(result.data);
        } else {
            showAlert('search-result', `검색 실패: ${result.error || '알 수 없는 오류'}`, 'danger');
        }
    } catch (error) {
        console.error('API 오류:', error);
        showAlert('search-result', `API 호출 중 오류: ${error.message}`, 'danger');
    }
}

// 채널 분석
async function analyzeChannel() {
    const url = document.getElementById('channel-url').value;
    if (!url) {
        showAlert('channel-result', 'URL을 입력해주세요.', 'warning');
        return;
    }

    showLoading('channel-result');
    try {
        const response = await fetch('/api/channel-info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_url: url })
        });

        const result = await response.json();
        console.log('채널 분석 결과:', result);

        if (result.success && result.data) {
            displayChannelResult(result.data);
        } else {
            showAlert('channel-result', `분석 실패: ${result.error || '알 수 없는 오류'}`, 'danger');
        }
    } catch (error) {
        console.error('API 오류:', error);
        showAlert('channel-result', `API 호출 중 오류: ${error.message}`, 'danger');
    }
}

// 자막 추출
async function extractTranscript() {
    const url = document.getElementById('transcript-url').value;
    if (!url) {
        showAlert('transcript-result', 'URL을 입력해주세요.', 'warning');
        return;
    }

    showLoading('transcript-result');
    try {
        const response = await fetch('/api/transcript', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url })
        });

        const result = await response.json();
        console.log('자막 추출 결과:', result);

        if (result.success && result.data) {
            displayTranscriptResult(result.data);
        } else {
            showAlert('transcript-result', `추출 실패: ${result.error || '알 수 없는 오류'}`, 'danger');
        }
    } catch (error) {
        console.error('API 오류:', error);
        showAlert('transcript-result', `API 호출 중 오류: ${error.message}`, 'danger');
    }
}

// 유사도 검색
async function searchSimilar() {
    const query = document.getElementById('similarity-query').value;
    if (!query) {
        showAlert('similarity-result', '검색어를 입력해주세요.', 'warning');
        return;
    }

    showLoading('similarity-result');
    try {
        const response = await fetch('/api/search-similar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        });

        const result = await response.json();
        console.log('유사도 검색 결과:', result);

        if (result.success && result.data) {
            displaySimilarityResult(result.data);
        } else {
            showAlert('similarity-result', `검색 실패: ${result.error || '알 수 없는 오류'}`, 'danger');
        }
    } catch (error) {
        console.error('API 오류:', error);
        showAlert('similarity-result', `API 호출 중 오류: ${error.message}`, 'danger');
    }
}

// 단일 영상 저장
async function saveSingleVideo() {
    const url = document.getElementById('single-video-url').value;
    if (!url) {
        showAlert('single-video-result', 'URL을 입력해주세요.', 'warning');
        return;
    }

    showLoading('single-video-result');
    try {
        const response = await fetch('/api/save-single-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_url: url })
        });

        const result = await response.json();
        console.log('단일 영상 저장 결과:', result);

        if (result.success) {
            showAlert('single-video-result', '단일 영상 저장이 완료되었습니다.', 'success');
        } else {
            showAlert('single-video-result', `저장 실패: ${result.error || '알 수 없는 오류'}`, 'danger');
        }
    } catch (error) {
        console.error('API 오류:', error);
        showAlert('single-video-result', `API 호출 중 오류: ${error.message}`, 'danger');
    }
}

// 결과 표시 함수들
function displaySearchResults(videos) {
    const container = document.getElementById('search-result');
    
    if (!Array.isArray(videos) || videos.length === 0) {
        container.innerHTML = '<div class="alert alert-info">검색 결과가 없습니다.</div>';
        return;
    }

    let html = '<div class="card"><div class="card-header"><h5><i class="fas fa-youtube me-2"></i>검색 결과 (' + videos.length + '개)</h5></div><div class="card-body">';
    
    videos.forEach((video, index) => {
        let videoId = '';
        if (video.url) {
            const urlMatch = video.url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
            videoId = urlMatch ? urlMatch[1] : '';
        }
        
        const thumbnailUrl = video.thumbnailUrl || (videoId ? `https://img.youtube.com/vi/${videoId}/mqdefault.jpg` : '');
        
        html += `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-3">
                            <img src="${thumbnailUrl}" class="img-fluid rounded" alt="썸네일">
                        </div>
                        <div class="col-md-9">
                            <h6 class="card-title">${video.title || '제목 없음'}</h6>
                            <p class="card-text">
                                <strong>채널:</strong> ${video.channelName || '채널명 없음'}<br>
                                <strong>조회수:</strong> ${video.viewCount ? video.viewCount.toLocaleString() : 'N/A'}<br>
                                <strong>좋아요:</strong> ${video.likeCount ? video.likeCount.toLocaleString() : 'N/A'}
                            </p>
                            <a href="${video.url || '#'}" target="_blank" class="btn btn-sm btn-outline-primary">
                                <i class="fab fa-youtube me-1"></i>YouTube에서 보기
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += '</div></div>';
    container.innerHTML = html;
}

function displayChannelResult(data) {
    const container = document.getElementById('channel-result');
    
    if (data.error) {
        showAlert('channel-result', data.error, 'warning');
        return;
    }

    const html = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-tv me-2"></i>채널 정보</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <img src="${data.channelThumbnail || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTUwIiBoZWlnaHQ9IjE1MCIgdmlld0JveD0iMCAwIDE1MCAxNTAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxNTAiIGhlaWdodD0iMTUwIiBmaWxsPSIjRjVGNUY1Ii8+CjxwYXRoIGQ9Ik03NSA3NUM3NSA3NSA3NSA3NSA3NSA3NVoiIGZpbGw9IiM5OTk5OTkiLz4KPC9zdmc+'}" 
                             class="img-fluid rounded" alt="채널 썸네일">
                    </div>
                    <div class="col-md-9">
                        <h5>${data.channelTitle || '채널명 없음'}</h5>
                        <p><strong>구독자:</strong> ${data.subscriberCount ? data.subscriberCount.toLocaleString() : 'N/A'}</p>
                        <p><strong>영상 수:</strong> ${data.videoCount || 'N/A'}</p>
                        <p><strong>총 조회수:</strong> ${data.viewCount ? data.viewCount.toLocaleString() : 'N/A'}</p>
                        <a href="${data.channelUrl || '#'}" target="_blank" class="btn btn-sm btn-outline-primary">
                            <i class="fab fa-youtube me-1"></i>채널 방문
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

function displayTranscriptResult(data) {
    const container = document.getElementById('transcript-result');
    
    if (data.error || (data.transcript && (data.transcript.includes('자막 추출 실패') || data.transcript.includes('자막을 찾을 수 없')))) {
        const errorMsg = data.error || data.transcript || '자막 추출에 실패했습니다.';
        showAlert('transcript-result', errorMsg, 'warning');
        return;
    }

    const url = document.getElementById('transcript-url').value;
    const videoIdMatch = url.match(/(?:v=|\/)([0-9A-Za-z_-]{11})/);
    const videoId = videoIdMatch ? videoIdMatch[1] : 'unknown';

    const html = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-closed-captioning me-2"></i>자막 내용</h5>
            </div>
            <div class="card-body">
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>
                    <strong>자막 추출 성공!</strong>
                </div>
                <div class="row">
                    <div class="col-md-3">
                        <img src="https://img.youtube.com/vi/${videoId}/mqdefault.jpg" 
                             class="img-fluid rounded" alt="썸네일">
                    </div>
                    <div class="col-md-9">
                        <h6>${data.title || '제목 없음'}</h6>
                        <p><strong>자막 길이:</strong> ${data.transcript ? data.transcript.length : 0}자</p>
                    </div>
                </div>
                <div class="mt-3">
                    <h6>전체 자막</h6>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 400px; overflow-y: auto;">
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">${data.transcript || '자막을 찾을 수 없습니다.'}</pre>
                    </div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

function displaySimilarityResult(data) {
    const container = document.getElementById('similarity-result');
    
    if (data.error) {
        showAlert('similarity-result', data.error, 'warning');
        return;
    }

    const html = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-search me-2"></i>유사도 검색 결과</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-3">
                        <img src="https://img.youtube.com/vi/${data.video_id}/mqdefault.jpg" 
                             class="img-fluid rounded" alt="썸네일">
                    </div>
                    <div class="col-md-9">
                        <h6>유사도 점수: ${data.score ? (data.score * 100).toFixed(2) + '%' : 'N/A'}</h6>
                        <p><strong>비디오 ID:</strong> ${data.video_id}</p>
                        <p><strong>청크 인덱스:</strong> ${data.chunk_index}</p>
                        <a href="${data.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                            <i class="fab fa-youtube me-1"></i>영상 보기
                        </a>
                    </div>
                </div>
                <div class="mt-3">
                    <h6>유사한 자막 내용</h6>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; max-height: 300px; overflow-y: auto;">
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">${data.chunk_text || '내용을 찾을 수 없습니다.'}</pre>
                    </div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
} 

// AI 채팅 기능
let chatHistory = [];

// 채팅 메시지 전송
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) {
        alert('메시지를 입력해주세요.');
        return;
    }

    // 사용자 메시지 추가
    addChatMessage('user', message);
    input.value = '';

    // 로딩 메시지 표시
    const loadingId = addChatMessage('assistant', '🤔 생각 중...', 'loading');

    try {
        // MCP 서버들과 연동하여 응답 생성
        const response = await processChatMessage(message);
        
        // 로딩 메시지 제거하고 응답 표시
        removeChatMessage(loadingId);
        addChatMessage('assistant', response);
        
    } catch (error) {
        console.error('Chat error:', error);
        removeChatMessage(loadingId);
        addChatMessage('assistant', '❌ 오류가 발생했습니다: ' + error.message);
    }
}

// 채팅 메시지 처리 (MCP 서버 연동)
async function processChatMessage(message) {
    const lowerMessage = message.toLowerCase();
    
    // YouTube 검색 관련
    if (lowerMessage.includes('검색') || lowerMessage.includes('찾아') || lowerMessage.includes('영상')) {
        const query = extractQuery(message);
        if (query) {
            const result = await callYouTubeSearch(query);
            return formatYouTubeSearchResponse(result, query);
        }
    }
    
    // 비디오 검색 관련
    if (lowerMessage.includes('비디오') || lowerMessage.includes('동영상') || lowerMessage.includes('프레임')) {
        const query = extractQuery(message);
        if (query) {
            const result = await callVideoSearch(query);
            return formatVideoSearchResponse(result, query);
        }
    }
    
    // 채널 분석 관련
    if (lowerMessage.includes('채널') || lowerMessage.includes('분석') || lowerMessage.includes('정보')) {
        const query = extractQuery(message);
        if (query) {
            const result = await callChannelAnalysis(query);
            return formatChannelAnalysisResponse(result, query);
        }
    }
    
    // 트렌딩 분석
    if (lowerMessage.includes('트렌딩') || lowerMessage.includes('인기') || lowerMessage.includes('트렌드')) {
        const result = await callTrendingAnalysis();
        return formatTrendingResponse(result);
    }
    
    // 기본 응답
    return `안녕하세요! YouTube AI 어시스턴트입니다. 다음과 같은 요청을 도와드릴 수 있습니다:

🔍 **YouTube 검색**: "강아지 영상 찾아줘", "요리 영상 검색해줘"
🎥 **비디오 분석**: "강아지가 뛰는 장면 찾아줘", "비디오에서 사람이 걷는 장면 검색"
📺 **채널 분석**: "인기 채널 분석해줘", "채널 정보 알려줘"
📈 **트렌딩**: "트렌딩 영상 알려줘", "인기 콘텐츠 분석해줘"

어떤 도움이 필요하신가요?`;
}

// 쿼리 추출
function extractQuery(message) {
    // 따옴표로 감싸진 부분 추출
    const quotedMatch = message.match(/[""]([^""]+)[""]/);
    if (quotedMatch) {
        return quotedMatch[1];
    }
    
    // "~해줘" 앞의 내용 추출
    const actionMatch = message.match(/(.+?)(?:해줘|찾아줘|검색해줘|알려줘)/);
    if (actionMatch) {
        return actionMatch[1].trim();
    }
    
    // 마지막 명사 추출 시도
    const words = message.split(/\s+/);
    return words[words.length - 1];
}

// YouTube 검색 API 호출
async function callYouTubeSearch(query) {
    try {
        const response = await fetch('http://localhost:3000/api/youtube/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, max_results: 5 })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('YouTube search error:', error);
        throw new Error('YouTube 검색 중 오류가 발생했습니다.');
    }
}

// 비디오 검색 API 호출
async function callVideoSearch(query) {
    try {
        const response = await fetch('http://localhost:3000/api/search-video', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, top_k: 5 })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Video search error:', error);
        throw new Error('비디오 검색 중 오류가 발생했습니다.');
    }
}

// 채널 분석 API 호출
async function callChannelAnalysis(query) {
    try {
        const response = await fetch('http://localhost:3000/api/channel-info', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ video_url: query })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Channel analysis error:', error);
        throw new Error('채널 분석 중 오류가 발생했습니다.');
    }
}

// 트렌딩 분석 API 호출
async function callTrendingAnalysis() {
    try {
        const response = await fetch('http://localhost:3000/api/trending-analysis', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ region: 'KR', category: 'all' })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Trending analysis error:', error);
        throw new Error('트렌딩 분석 중 오류가 발생했습니다.');
    }
}

// YouTube 검색 응답 포맷
function formatYouTubeSearchResponse(result, query) {
    if (!result.success || !result.data.results) {
        return `❌ "${query}" 검색 결과를 가져오는데 실패했습니다.`;
    }
    
    const videos = result.data.results;
    let response = `🔍 **"${query}" 검색 결과** (${videos.length}개)\n\n`;
    
    videos.forEach((video, index) => {
        response += `${index + 1}. **${video.title}**\n`;
        response += `   📺 ${video.channel} | 👁️ ${video.views} | ⏱️ ${video.duration}\n`;
        response += `   🔗 ${video.url}\n\n`;
    });
    
    return response;
}

// 비디오 검색 응답 포맷
function formatVideoSearchResponse(result, query) {
    if (!result.success || !result.data.results) {
        return `❌ "${query}" 비디오 검색 결과를 가져오는데 실패했습니다.`;
    }
    
    const videos = result.data.results;
    let response = `🎥 **"${query}" 비디오 검색 결과** (${videos.length}개)\n\n`;
    
    videos.forEach((video, index) => {
        const timestamp = formatTimestamp(video.timestamp);
        const similarity = (video.similarity * 100).toFixed(1);
        response += `${index + 1}. **${video.video_id}**\n`;
        response += `   ⏰ ${timestamp} | 🎯 유사도: ${similarity}%\n`;
        response += `   📁 ${video.video_path}\n\n`;
    });
    
    return response;
}

// 채널 분석 응답 포맷
function formatChannelAnalysisResponse(result, query) {
    if (!result.success || !result.data) {
        return `❌ "${query}" 채널 정보를 가져오는데 실패했습니다.`;
    }
    
    const channel = result.data;
    let response = `📺 **"${query}" 채널 정보**\n\n`;
    response += `🏷️ **이름**: ${channel.name}\n`;
    response += `👥 **구독자**: ${channel.subscribers}\n`;
    response += `🎬 **비디오 수**: ${channel.videos}\n`;
    response += `📝 **설명**: ${channel.description}\n`;
    response += `📅 **생성일**: ${channel.created_at}\n`;
    
    return response;
}

// 트렌딩 응답 포맷
function formatTrendingResponse(result) {
    if (!result.success || !result.data.videos) {
        return `❌ 트렌딩 분석 결과를 가져오는데 실패했습니다.`;
    }
    
    const videos = result.data.videos;
    let response = `📈 **트렌딩 영상 분석** (${videos.length}개)\n\n`;
    
    videos.forEach((video, index) => {
        response += `${index + 1}. **${video.title}**\n`;
        response += `   📺 ${video.channel} | 👁️ ${video.views}\n`;
        response += `   🏷️ 카테고리: ${video.category}\n\n`;
    });
    
    return response;
}

// 채팅 메시지 추가
function addChatMessage(type, content, className = '') {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    const messageId = 'msg-' + Date.now();
    
    messageDiv.id = messageId;
    messageDiv.className = `chat-message ${type} ${className}`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div>${content}</div>
        <div class="chat-timestamp">${timestamp}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // 채팅 히스토리에 저장
    chatHistory.push({ id: messageId, type, content, timestamp });
    
    return messageId;
}

// 채팅 메시지 제거
function removeChatMessage(messageId) {
    const messageElement = document.getElementById(messageId);
    if (messageElement) {
        messageElement.remove();
    }
}

// Enter 키로 메시지 전송
document.addEventListener('DOMContentLoaded', function() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
    
    // 초기 환영 메시지
    setTimeout(() => {
        addChatMessage('assistant', '안녕하세요! YouTube AI 어시스턴트입니다. 🎥\n\n무엇을 도와드릴까요?');
    }, 500);
}); 
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
    const query = document.getElementById('youtubeSearchQuery').value.trim();
    if (!query) {
        alert('검색어를 입력해주세요.');
        return;
    }

    showLoading('youtubeSearchLoading');
    hideResult('youtubeSearchResult');

    try {
        const response = await fetch(`${API_BASE_URL}/api/youtube/search`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query })
        });

        const videos = await response.json();
        displayYouTubeSearchResult(videos);
    } catch (error) {
        console.error('Error:', error);
        displayError('youtubeSearchResult', 'YouTube 검색 중 오류가 발생했습니다.');
    } finally {
        hideLoading('youtubeSearchLoading');
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
                <img src="${video.thumbnail_url}" class="card-img-top thumbnail" alt="${video.title}">
                <div class="card-body">
                    <h6 class="card-title">${video.title}</h6>
                    <p class="card-text text-muted">${video.channel_name}</p>
                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">
                            <i class="fas fa-eye"></i> ${formatNumber(video.view_count)}
                        </small>
                        <small class="text-muted">
                            <i class="fas fa-thumbs-up"></i> ${formatNumber(video.like_count)}
                        </small>
                    </div>
                </div>
                <div class="card-footer">
                    <a href="${video.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                        <i class="fab fa-youtube"></i> 보기
                    </a>
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
function showLoading(elementId) {
    document.getElementById(elementId).style.display = 'block';
}

function hideLoading(elementId) {
    document.getElementById(elementId).style.display = 'none';
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
    document.getElementById('searchQuery').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') searchSimilar();
    });
    
    document.getElementById('youtubeSearchQuery').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') searchYouTube();
    });
    
    document.getElementById('channelVideoUrl').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') getChannelInfo();
    });
    
    document.getElementById('transcriptUrl').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') getTranscript();
    });
    
    document.getElementById('saveChannelId').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') saveChannel();
    });
    
    document.getElementById('single-video-url').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') previewTranscript();
    });
    
    document.getElementById('semantic-video-url').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') saveSemanticVideo();
    });
    
    document.getElementById('compare-video-url').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') compareChunking();
    });
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
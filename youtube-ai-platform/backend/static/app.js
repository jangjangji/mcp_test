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
function displayTranscriptResult(result) {
    const container = document.getElementById('transcriptResult');
    
    if (result.error) {
        container.innerHTML = `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-triangle"></i>
                ${result.error}
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5><i class="fas fa-closed-captioning"></i> 자막 내용</h5>
            </div>
            <div class="card-body">
                <div class="border p-3 bg-light" style="max-height: 400px; overflow-y: auto;">
                    <p class="mb-0">${result.transcript}</p>
                </div>
            </div>
        </div>
    `;
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
}); 
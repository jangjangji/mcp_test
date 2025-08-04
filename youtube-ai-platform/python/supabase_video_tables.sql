-- 비디오 프레임 임베딩 테이블 생성
CREATE TABLE video_frames (
    id BIGSERIAL PRIMARY KEY,
    video_id TEXT NOT NULL,
    video_path TEXT NOT NULL,
    frame_timestamp DOUBLE PRECISION NOT NULL,
    embedding VECTOR(512) NOT NULL,
    added_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성 (검색 성능 향상)
CREATE INDEX idx_video_frames_video_id ON video_frames(video_id);
CREATE INDEX idx_video_frames_timestamp ON video_frames(frame_timestamp);
CREATE INDEX idx_video_frames_embedding ON video_frames USING ivfflat (embedding vector_cosine_ops);

-- 유사도 검색을 위한 RPC 함수 생성
CREATE OR REPLACE FUNCTION match_video_frames(
    input_vector VECTOR(512),
    match_count INTEGER DEFAULT 5
)
RETURNS TABLE (
    video_id TEXT,
    video_path TEXT,
    frame_timestamp DOUBLE PRECISION,
    similarity DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vf.video_id,
        vf.video_path,
        vf.frame_timestamp,
        1 - (vf.embedding <=> input_vector) as similarity
    FROM video_frames vf
    ORDER BY vf.embedding <=> input_vector
    LIMIT match_count;
END;
$$;

-- 테이블에 RLS 정책 설정 (선택사항)
ALTER TABLE video_frames ENABLE ROW LEVEL SECURITY;

-- 모든 사용자가 읽기/쓰기 가능하도록 정책 설정
CREATE POLICY "Allow all operations on video_frames" ON video_frames
    FOR ALL USING (true)
    WITH CHECK (true); 
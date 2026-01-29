-- SYNK 창작자 스튜디오 Supabase 스키마
-- 버전: v1.0
-- 작성일: 2024년

-- ============================================
-- 1. 사용자 인증 (Supabase Auth 사용)
-- ============================================
-- Supabase Auth를 사용하므로 별도 테이블 불필요
-- auth.users 테이블 자동 생성됨

-- ============================================
-- 2. 작품 (Works) 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS works (
    work_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    creator_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- 작품 정보
    title VARCHAR(50) NOT NULL,
    description VARCHAR(500) NOT NULL,
    thumbnail_url TEXT,
    tags TEXT[] DEFAULT '{}', -- 태그 배열 (최대 10개)
    
    -- 설정
    target_audience VARCHAR(10) NOT NULL DEFAULT 'all' CHECK (target_audience IN ('all', 'male', 'female')),
    visibility VARCHAR(10) NOT NULL DEFAULT 'private' CHECK (visibility IN ('public', 'private', 'unlisted')),
    is_adult BOOLEAN DEFAULT FALSE,
    
    -- 통계
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    play_count INTEGER DEFAULT 0,
    
    -- 메타
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    
    -- 인덱스
    CONSTRAINT works_title_length CHECK (char_length(title) <= 50),
    CONSTRAINT works_description_length CHECK (char_length(description) <= 500),
    CONSTRAINT works_tags_limit CHECK (array_length(tags, 1) <= 10)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_works_creator_id ON works(creator_id);
CREATE INDEX IF NOT EXISTS idx_works_visibility ON works(visibility);
CREATE INDEX IF NOT EXISTS idx_works_published_at ON works(published_at) WHERE published_at IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_works_tags ON works USING GIN(tags);

-- updated_at 자동 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_works_updated_at
    BEFORE UPDATE ON works
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 3. 캐릭터 (Characters) 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS characters (
    character_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    
    -- 캐릭터 정보
    name VARCHAR(35) NOT NULL,
    profile_image_url TEXT,
    prompt TEXT NOT NULL, -- 캐릭터 프롬프트 (최대 16,000자)
    
    -- 메타
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT characters_name_length CHECK (char_length(name) <= 35),
    CONSTRAINT characters_prompt_length CHECK (char_length(prompt) <= 16000)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_characters_work_id ON characters(work_id);

CREATE TRIGGER update_characters_updated_at
    BEFORE UPDATE ON characters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. 이미지 갤러리 (Gallery Images) 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS gallery_images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    
    -- 이미지 정보
    character_name VARCHAR(35), -- NULL이면 배경/기타
    keyword VARCHAR(30) NOT NULL, -- 영문, 숫자, 언더바만 사용
    image_url TEXT NOT NULL,
    description VARCHAR(100), -- 설명 (최대 100자)
    
    -- 자동 생성
    usage_code TEXT NOT NULL, -- "{{img::캐릭터명::키워드}}" 형식
    preview_url TEXT NOT NULL, -- 미리보기 링크
    
    -- 메타
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT gallery_images_keyword_format CHECK (keyword ~ '^[a-zA-Z0-9_]+$'), -- 영문, 숫자, 언더바만
    CONSTRAINT gallery_images_description_length CHECK (char_length(description) <= 100 OR description IS NULL)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_gallery_images_work_id ON gallery_images(work_id);
CREATE INDEX IF NOT EXISTS idx_gallery_images_character_name ON gallery_images(character_name);
CREATE INDEX IF NOT EXISTS idx_gallery_images_keyword ON gallery_images(keyword);

-- ============================================
-- 5. 로어북 (Lorebook) 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS lorebook_entries (
    entry_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    
    -- 로어 정보
    name VARCHAR(80) NOT NULL,
    keywords TEXT[] NOT NULL DEFAULT '{}', -- 활성화 키워드 배열
    content TEXT NOT NULL, -- 로어 내용 (최대 4,500자)
    priority INTEGER NOT NULL DEFAULT 0, -- 우선순위 (낮을수록 높음)
    
    -- 고급 조건 (JSON)
    conditions JSONB, -- {min_intimacy, min_turns, required_character}
    
    -- 메타
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT lorebook_entries_name_length CHECK (char_length(name) <= 80),
    CONSTRAINT lorebook_entries_content_length CHECK (char_length(content) <= 4500)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_lorebook_entries_work_id ON lorebook_entries(work_id);
CREATE INDEX IF NOT EXISTS idx_lorebook_entries_priority ON lorebook_entries(work_id, priority);
CREATE INDEX IF NOT EXISTS idx_lorebook_entries_keywords ON lorebook_entries USING GIN(keywords);

CREATE TRIGGER update_lorebook_entries_updated_at
    BEFORE UPDATE ON lorebook_entries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 6. 오프닝 (Openings) 테이블
-- ============================================
CREATE TABLE IF NOT EXISTS openings (
    opening_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    work_id UUID NOT NULL REFERENCES works(work_id) ON DELETE CASCADE,
    
    -- 오프닝 정보
    title VARCHAR(50) NOT NULL,
    content TEXT NOT NULL, -- 내용 (최대 5,500자)
    is_default BOOLEAN DEFAULT FALSE, -- 기본 오프닝 여부
    order_index INTEGER NOT NULL DEFAULT 0, -- 표시 순서
    
    -- 메타
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 제약 조건
    CONSTRAINT openings_title_length CHECK (char_length(title) <= 50),
    CONSTRAINT openings_content_length CHECK (char_length(content) <= 5500)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_openings_work_id ON openings(work_id);
CREATE INDEX IF NOT EXISTS idx_openings_is_default ON openings(work_id, is_default);
CREATE INDEX IF NOT EXISTS idx_openings_order ON openings(work_id, order_index);

CREATE TRIGGER update_openings_updated_at
    BEFORE UPDATE ON openings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 7. Row Level Security (RLS) 정책
-- ============================================

-- RLS 활성화
ALTER TABLE works ENABLE ROW LEVEL SECURITY;
ALTER TABLE characters ENABLE ROW LEVEL SECURITY;
ALTER TABLE gallery_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE lorebook_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE openings ENABLE ROW LEVEL SECURITY;

-- Works 정책
-- 1. 자신이 만든 작품은 모두 볼 수 있음
CREATE POLICY "Users can view their own works"
    ON works FOR SELECT
    USING (auth.uid() = creator_id);

-- 2. 공개된 작품은 모두 볼 수 있음
CREATE POLICY "Anyone can view public works"
    ON works FOR SELECT
    USING (visibility = 'public' AND published_at IS NOT NULL);

-- 3. 링크 공유 작품은 모두 볼 수 있음 (unlisted)
CREATE POLICY "Anyone can view unlisted works"
    ON works FOR SELECT
    USING (visibility = 'unlisted');

-- 4. 자신이 만든 작품만 수정 가능
CREATE POLICY "Users can update their own works"
    ON works FOR UPDATE
    USING (auth.uid() = creator_id);

-- 5. 자신이 만든 작품만 삭제 가능
CREATE POLICY "Users can delete their own works"
    ON works FOR DELETE
    USING (auth.uid() = creator_id);

-- 6. 누구나 작품 생성 가능
CREATE POLICY "Anyone can create works"
    ON works FOR INSERT
    WITH CHECK (auth.uid() = creator_id);

-- Characters 정책
-- 1. 작품을 볼 수 있으면 캐릭터도 볼 수 있음
CREATE POLICY "Users can view characters of accessible works"
    ON characters FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM works
            WHERE works.work_id = characters.work_id
            AND (
                works.creator_id = auth.uid()
                OR works.visibility = 'public' AND works.published_at IS NOT NULL
                OR works.visibility = 'unlisted'
            )
        )
    );

-- 2. 자신의 작품 캐릭터만 수정/삭제 가능
CREATE POLICY "Users can manage characters of their own works"
    ON characters FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM works
            WHERE works.work_id = characters.work_id
            AND works.creator_id = auth.uid()
        )
    );

-- Gallery Images 정책
-- 1. 작품을 볼 수 있으면 이미지도 볼 수 있음
CREATE POLICY "Users can view images of accessible works"
    ON gallery_images FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM works
            WHERE works.work_id = gallery_images.work_id
            AND (
                works.creator_id = auth.uid()
                OR works.visibility = 'public' AND works.published_at IS NOT NULL
                OR works.visibility = 'unlisted'
            )
        )
    );

-- 2. 자신의 작품 이미지만 관리 가능
CREATE POLICY "Users can manage images of their own works"
    ON gallery_images FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM works
            WHERE works.work_id = gallery_images.work_id
            AND works.creator_id = auth.uid()
        )
    );

-- Lorebook Entries 정책
-- 1. 작품을 볼 수 있으면 로어북도 볼 수 있음
CREATE POLICY "Users can view lorebook of accessible works"
    ON lorebook_entries FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM works
            WHERE works.work_id = lorebook_entries.work_id
            AND (
                works.creator_id = auth.uid()
                OR works.visibility = 'public' AND works.published_at IS NOT NULL
                OR works.visibility = 'unlisted'
            )
        )
    );

-- 2. 자신의 작품 로어북만 관리 가능
CREATE POLICY "Users can manage lorebook of their own works"
    ON lorebook_entries FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM works
            WHERE works.work_id = lorebook_entries.work_id
            AND works.creator_id = auth.uid()
        )
    );

-- Openings 정책
-- 1. 작품을 볼 수 있으면 오프닝도 볼 수 있음
CREATE POLICY "Users can view openings of accessible works"
    ON openings FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM works
            WHERE works.work_id = openings.work_id
            AND (
                works.creator_id = auth.uid()
                OR works.visibility = 'public' AND works.published_at IS NOT NULL
                OR works.visibility = 'unlisted'
            )
        )
    );

-- 2. 자신의 작품 오프닝만 관리 가능
CREATE POLICY "Users can manage openings of their own works"
    ON openings FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM works
            WHERE works.work_id = openings.work_id
            AND works.creator_id = auth.uid()
        )
    );

-- ============================================
-- 8. 함수 및 뷰
-- ============================================

-- 작품 통계 업데이트 함수
CREATE OR REPLACE FUNCTION increment_work_stat(work_uuid UUID, stat_type TEXT)
RETURNS VOID AS $$
BEGIN
    IF stat_type = 'view' THEN
        UPDATE works SET view_count = view_count + 1 WHERE work_id = work_uuid;
    ELSIF stat_type = 'like' THEN
        UPDATE works SET like_count = like_count + 1 WHERE work_id = work_uuid;
    ELSIF stat_type = 'play' THEN
        UPDATE works SET play_count = play_count + 1 WHERE work_id = work_uuid;
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 공개 작품 목록 뷰 (성능 최적화)
CREATE OR REPLACE VIEW public_works_view AS
SELECT 
    work_id,
    creator_id,
    title,
    description,
    thumbnail_url,
    tags,
    target_audience,
    is_adult,
    view_count,
    like_count,
    play_count,
    published_at
FROM works
WHERE visibility = 'public' AND published_at IS NOT NULL;

-- ============================================
-- 9. 기존 시스템 테이블 (MVP 채팅 시스템용)
-- ============================================

-- 장소 (Locations) 테이블
CREATE TABLE IF NOT EXISTS locations (
    location_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_locations_name ON locations(name);

-- 기존 캐릭터 (Legacy Characters) 테이블
-- 주의: 창작자 스튜디오의 characters 테이블과는 별개
CREATE TABLE IF NOT EXISTS legacy_characters (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
    
    -- JSON 필드들
    personality TEXT,
    speech_style TEXT,
    speech_examples TEXT, -- JSON array
    background TEXT,
    secrets TEXT, -- JSON array
    
    user_relationship VARCHAR(50) DEFAULT 'stranger',
    dominance_default REAL DEFAULT 0.0,
    
    emotion_triggers TEXT, -- JSON object
    sensitive_topics TEXT, -- JSON array
    
    tags TEXT, -- JSON array
    ability VARCHAR(100),
    ability_rank VARCHAR(10),
    
    default_emotion VARCHAR(50) DEFAULT 'neutral',
    default_posture VARCHAR(50) DEFAULT 'standing',
    voice_tone VARCHAR(50) DEFAULT 'normal',
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_legacy_characters_location ON legacy_characters(location);
CREATE INDEX IF NOT EXISTS idx_legacy_characters_name ON legacy_characters(name);

CREATE TRIGGER update_legacy_characters_updated_at
    BEFORE UPDATE ON legacy_characters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 관계 데이터 (Relationships) 테이블
CREATE TABLE IF NOT EXISTS relationships (
    user_id VARCHAR(100),
    character_id VARCHAR(100) REFERENCES legacy_characters(id) ON DELETE CASCADE,
    
    -- 친밀도
    intimacy REAL DEFAULT 0.0,
    
    -- Dominance
    dominance_score REAL DEFAULT 0.0,
    dominance_history TEXT, -- JSON array
    
    -- 감정 통계 (JSON)
    emotional_stats TEXT, -- JSON object
    
    -- 핵심 기억 (JSON)
    core_memories TEXT, -- JSON array
    
    -- 트리거 키워드 (JSON)
    trigger_keywords TEXT, -- JSON array
    
    -- 메타데이터
    total_turns INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    PRIMARY KEY (user_id, character_id)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_relationships_user_id ON relationships(user_id);
CREATE INDEX IF NOT EXISTS idx_relationships_character_id ON relationships(character_id);

CREATE TRIGGER update_relationships_updated_at
    BEFORE UPDATE ON relationships
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 유저 프로필 (User Profiles) 테이블
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id VARCHAR(100) PRIMARY KEY,
    
    -- 기본 정보
    nickname VARCHAR(100),
    gender VARCHAR(20),
    
    -- 능력 정보
    ability_name VARCHAR(100),
    ability_description TEXT,
    ability_rank VARCHAR(10),
    ability_type VARCHAR(50),
    
    -- 성격/특성
    personality_traits TEXT, -- JSON array
    speech_style TEXT,
    
    -- 캐릭터별 인상 (JSON)
    character_impressions TEXT, -- JSON object
    
    -- 행동 히스토리 (JSON)
    key_actions TEXT, -- JSON array
    mentioned_facts TEXT, -- JSON array
    
    -- 선호도
    likes TEXT, -- JSON array
    dislikes TEXT, -- JSON array
    
    -- 통계
    total_turns INTEGER DEFAULT 0,
    favorite_character VARCHAR(100),
    
    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 스토리 요약 (Story Summaries) 테이블
CREATE TABLE IF NOT EXISTS story_summaries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    user_id VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL,
    
    -- 턴 정보
    turn_number INTEGER NOT NULL,
    turn_id VARCHAR(100) NOT NULL,
    
    -- 대화 내용
    user_message TEXT,
    character_response TEXT,
    character_id VARCHAR(100),
    character_name VARCHAR(100),
    
    -- AI 분석 요약
    summary TEXT,
    key_events TEXT, -- JSON array
    emotional_tone VARCHAR(50),
    
    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_story_summaries_session_id ON story_summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_story_summaries_user_id ON story_summaries(user_id);
CREATE INDEX IF NOT EXISTS idx_story_summaries_location ON story_summaries(location);
CREATE INDEX IF NOT EXISTS idx_story_summaries_turn_id ON story_summaries(turn_id);

-- ============================================
-- 10. 기존 시스템 RLS 정책
-- ============================================

-- Locations 정책 (공개 읽기)
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view locations"
    ON locations FOR SELECT
    USING (true);

-- Legacy Characters 정책 (공개 읽기)
ALTER TABLE legacy_characters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view legacy characters"
    ON legacy_characters FOR SELECT
    USING (true);

-- Relationships 정책 (자신의 관계만 조회)
ALTER TABLE relationships ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own relationships"
    ON relationships FOR SELECT
    USING (true); -- MVP에서는 모든 사용자가 조회 가능 (나중에 user_id 기반으로 제한 가능)

CREATE POLICY "Users can manage their own relationships"
    ON relationships FOR ALL
    USING (true); -- MVP에서는 모든 사용자가 수정 가능

-- User Profiles 정책
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own profile"
    ON user_profiles FOR SELECT
    USING (true); -- MVP에서는 모든 사용자가 조회 가능

CREATE POLICY "Users can manage their own profile"
    ON user_profiles FOR ALL
    USING (true); -- MVP에서는 모든 사용자가 수정 가능

-- Story Summaries 정책
ALTER TABLE story_summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own story summaries"
    ON story_summaries FOR SELECT
    USING (true); -- MVP에서는 모든 사용자가 조회 가능

CREATE POLICY "Users can create their own story summaries"
    ON story_summaries FOR INSERT
    WITH CHECK (true);

-- ============================================
-- 완료 메시지
-- ============================================
-- 이 SQL 스크립트를 Supabase SQL Editor에서 실행하세요.
-- 실행 후 다음을 확인하세요:
-- 1. 모든 테이블이 생성되었는지
-- 2. RLS 정책이 활성화되었는지
-- 3. 인덱스가 생성되었는지
-- 
-- 주의사항:
-- - 창작자 스튜디오의 characters 테이블과 legacy_characters 테이블은 별개입니다
-- - legacy_characters는 기존 MVP 채팅 시스템용입니다
-- - works 테이블의 characters는 창작자 스튜디오용입니다

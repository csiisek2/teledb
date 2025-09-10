-- 테스트용 샘플 데이터
-- 실제 개인정보를 사용하지 마세요

INSERT INTO phone_data (phone_number, name, company, address, email, notes) VALUES
('01012345678', '홍길동', '삼성전자', '서울시 강남구 테헤란로 123', 'hong@samsung.com', '개발팀 팀장'),
('01098765432', '김영희', '네이버', '경기도 분당구 정자일로 95', 'kim@naver.com', '기획팀'),
('01011112222', '박민수', 'LG전자', '서울시 영등포구 여의대로 128', 'park@lg.com', '마케팅팀'),
('01033334444', '이수정', '카카오', '제주시 첨단로 242', 'lee@kakao.com', 'UX 디자이너'),
('01055556666', '최도현', '토스', '서울시 강남구 테헤란로 131', 'choi@toss.im', '백엔드 개발자');

-- 샘플 조회 로그 데이터
INSERT INTO query_logs (user_id, username, query_phone, found) VALUES
(123456789, 'admin_user', '01012345678', 1),
(987654321, 'test_user', '01099999999', 0),
(123456789, 'admin_user', '01098765432', 1),
(555555555, 'another_user', '01012345678', 1);
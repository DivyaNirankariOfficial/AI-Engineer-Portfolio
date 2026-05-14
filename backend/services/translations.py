# backend/services/translations.py

import os
import re
from services.groq_service import call_groq
from database import get_cached_translation, save_translation

def contains_japanese(text: str) -> bool:
    if not text: return False
    # Check for Hiragana, Katakana, or Kanji
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', text))

LABELS = {
    "ko": {
        "education": "학력",
        "experience": "경력",
        "skills": "스킬",
        "projects": "주요 프로젝트",
        "awards": "수상",
        "research": "연구/논문",
        "certificates": "자격증",
        "languages": "언어 능력",
        "current": "재직중",
        "left": "퇴직",
        "fulltime": "정규직",
        "freelance": "프리랜서",
        "individual": "개인",
        "developer": "개발자",
        "summary": "전문 분야 요약",
        "contact": "연락처",
        "visa": "비자 상태",
        "gender": "성별",
        "nationality": "국적",
        "phone": "연락처",
        "email": "이메일",
        "address": "주소",
        "dob": "생년월일",
        "age": "나이",
        "marital_status": "혼인 여부",
        "in": "에서",
        "overseas": "해외 거주",
        "cover_letter_title": "자기소개서",
        "salutation": "채용 담당자님께,",
        "valediction": "올림,",
        "role_label": "직책",
        "type_label": "고용 형태",
        "team_size_label": "팀 규모",
        "proj_name_label": "프로젝트명",
        "period_label": "기간",
        "tech_stack_label": "기술 스택",
        "outcomes_label": "성과",
        "remarks_label": "비고",
        "cert_exam_label": "자격증/시험",
        "generated_at": "작성일",
        "page_x_of_y": "페이지 {x} / {y}",
        "year": "년",
        "month": "월",
        "photo": "사진",
        "contact_alt": "연락처 (비상시)",
        "same_as_above": "동상",
        "entry": "입학",
        "graduation": "졸업",
        "as_of": "현재",
        "male": "남",
        "female": "여",
        "end_of_doc": "이상",
        "nationality_default": "인도",
        "wechat": "위챗",
        "photo_alt": "사진",
        "photo_placeholder": "사진 (28x36mm)",
        "category_label": "분류",
        "skills_tools_label": "기술 / 도구",
        "proficiency_label": "숙련도",
        "proficient_label": "숙련",
        "job_duties_label": "주요 업무",
        "achievements_label": "주요 성과",
        "year_char": "년",
        "month_char": "월",
        "present": "현재",
        "writing_status": "작성 중",
        "cert_pending": "자격증 취득 중",
        "hobbies": "취미 및 특기",
        "gpa_label": "학점",
        "korean_level": "한국어 실력",
        "cl_growth": "성장과정",
        "cl_strengths": "성격의 장단점",
        "cl_motivation": "지원동기",
        "cl_goals": "입사 후 포부",
        "applicant_label": "지 원 자:",
        "confirmation_text": "위와 같이 사실과 틀림없음을 확인합니다.",
        "stamp_label": "(인)",
        "date_label": "이력서 작성일:",
        "jagi_title": "자　기　소　개　서"
    },
    "ja": {
        "education": "学歴",
        "experience": "職歴",
        "skills": "スキル・技術",
        "projects": "プロジェクト詳細",
        "awards": "受賞",
        "research": "研究・論文",
        "certificates": "免許・資格",
        "languages": "語学",
        "current": "在職中",
        "left": "退職",
        "fulltime": "正社員",
        "freelance": "フリーランス",
        "individual": "個人",
        "developer": "開発者",
        "summary": "自己PR",
        "contact": "連絡先",
        "visa": "在留資格",
        "gender": "性別",
        "nationality": "国籍",
        "phone": "電話",
        "email": "メールアドレス",
        "address": "住所",
        "dob": "生年月日",
        "age": "年齢",
        "marital_status": "配偶者",
        "in": "にて",
        "cover_letter_title": "添え状",
        "salutation": "採用担当者様",
        "valediction": "敬具",
        "role_label": "役割",
        "type_label": "雇用形態",
        "team_size_label": "チーム規模",
        "proj_name_label": "プロジェクト名",
        "period_label": "期間",
        "tech_stack_label": "使用技術",
        "outcomes_label": "成果",
        "remarks_label": "備考",
        "cert_exam_label": "資格・試験",
        "generated_at": "作成日",
        "page_x_of_y": "{x} / {y} ページ",
        "year": "年",
        "month": "月",
        "photo": "写真",
        "contact_alt": "連絡先",
        "same_as_above": "同上",
        "entry": "入学",
        "graduation": "卒業",
        "as_of": "現在",
        "male": "男",
        "female": "女",
        "end_of_doc": "以上",
        "rirekisho_title": "履 歴 書",
        "shokumu_title": "職務経歴書",
        "phonetic": "ふりがな",
        "name_label": "氏　名",
        "as_of": "現在",
        "entry": "入学",
        "graduation": "卒業",
        "joining": "入社",
        "resignation": "退社",
        "self_pr_label": "特技、自己PRなど",
        "commute_time_label": "通勤時間",
        "dependents_label": "扶養家族（配偶者を除く）",
        "spouse_label": "配偶者",
        "spouse_dependency_label": "配偶者の扶養義務",
        "desired_conditions_label": "本人希望記入欄",
        "instructions_label": "記入上の注意",
        "same_as_above": "同上",
        "contact_alt_label": "現住所以外に連絡を希望",
        "nationality_default": "インド",
        "wechat": "WeChat",
        "photo_alt": "証明写真",
        "photo_placeholder": "写真 (28x36mm)",
        "category_label": "カテゴリ",
        "skills_tools_label": "スキル・ツール",
        "proficiency_label": "熟練度",
        "proficient_label": "熟練",
        "job_duties_label": "担当業務",
        "achievements_label": "実績・成果",
        "year_char": "年",
        "month_char": "月",
        "present": "現在",
        "writing_status": "執筆中",
        "cert_pending": "資格取得中",
        "hobbies": "趣味・特記",
        "gpa_label": "GPA",
        "cl_growth": "成長過程",
        "cl_strengths": "長所・短所",
        "cl_motivation": "志望動機",
        "cl_goals": "入社後の抱負",
        "cl_header": "応募書類の送付につきまして"
    },
    "en": {
        "education": "Education",
        "experience": "Experience",
        "skills": "Skills / Tech",
        "projects": "Key Projects",
        "awards": "Awards",
        "research": "Research",
        "certificates": "Certifications",
        "languages": "Languages",
        "current": "Current",
        "left": "Resigned",
        "fulltime": "Full-time",
        "freelance": "Freelance",
        "individual": "Individual",
        "developer": "Developer",
        "summary": "Professional Summary",
        "contact": "Contact Information",
        "visa": "Visa",
        "gender": "Gender",
        "nationality": "Nationality",
        "phone": "Phone",
        "email": "Email",
        "address": "Address",
        "dob": "Date of Birth",
        "age": "Age",
        "marital_status": "Marital Status",
        "in": "in",
        "overseas": "Overseas",
        "cover_letter_title": "Cover Letter",
        "salutation": "To the Hiring Manager,",
        "valediction": "Sincerely,",
        "role_label": "Role",
        "type_label": "Nature",
        "team_size_label": "Team Size",
        "proj_name_label": "Project Name",
        "period_label": "Period",
        "tech_stack_label": "Tech Stack",
        "outcomes_label": "Summary / Achievements",
        "remarks_label": "Remarks",
        "cert_exam_label": "Cert/Exam",
        "generated_at": "Generated at",
        "page_x_of_y": "Page {x} of {y}",
        "year": "Year",
        "month": "Month",
        "photo": "Photo",
        "contact_alt": "Contact (Alt)",
        "same_as_above": "Same as above",
        "entry": "Entrance",
        "graduation": "Graduation",
        "joining": "Joined",
        "resignation": "Resigned",
        "as_of": "As of",
        "male": "Male",
        "female": "Female",
        "end_of_doc": "End of Document",
        "rirekisho_title": "Resume",
        "shokumu_title": "Professional Experience",
        "phonetic": "Furigana",
        "name_label": "Name",
        "self_pr_label": "Self PR",
        "commute_time_label": "Commute Time",
        "dependents_label": "Dependents",
        "spouse_label": "Spouse",
        "spouse_dependency_label": "Spouse Dependency",
        "desired_conditions_label": "Desired Conditions",
        "instructions_label": "Instructions",
        "contact_alt_label": "Emergency Contact",
        "nationality_default": "India",
        "wechat": "WeChat",
        "photo_alt": "ID Photo",
        "photo_placeholder": "ID Photo (28x36mm)",
        "category_label": "Category",
        "skills_tools_label": "Skills / Tools",
        "proficiency_label": "Proficiency",
        "proficient_label": "Proficient",
        "job_duties_label": "Responsibilities",
        "achievements_label": "Achievements",
        "year_char": "",
        "month_char": "",
        "present": "Present",
        "writing_status": "In Progress",
        "cert_pending": "In Progress",
        "hobbies": "Hobbies",
        "gpa_label": "GPA",
        "korean_level": "Korean Level",
        "cl_growth": "Background & Growth",
        "cl_strengths": "Strengths & Weaknesses",
        "cl_motivation": "Reason for Applying",
        "cl_goals": "Goals After Joining",
        "cl_header": "Application for Position",
        "skills_label": "Skills / Tech",
        "applicant_label": "Applicant:",
        "confirmation_text": "I hereby certify that the above information is true and correct.",
        "stamp_label": "(Sign)",
        "date_label": "Resume Date:",
        "jagi_title": "Self-Introduction (Cover Letter)"
    },
    "zh": {
        "education": "学历",
        "experience": "工作经验",
        "skills": "专业能力",
        "projects": "项目经验",
        "awards": "荣誉奖项",
        "research": "研究成果",
        "certificates": "资质证书",
        "languages": "语言能力",
        "current": "在职",
        "left": "离职",
        "fulltime": "全职",
        "freelance": "自由职业",
        "individual": "个人",
        "developer": "开发者",
        "summary": "个人简介",
        "contact": "联系方式",
        "visa": "在留资格",
        "gender": "性别",
        "nationality": "国籍",
        "phone": "联系电话",
        "email": "电子邮箱",
        "address": "通讯地址",
        "dob": "出生年月",
        "age": "年龄",
        "marital_status": "婚姻状况",
        "in": "于",
        "overseas": "海外居住",
        "cover_letter_title": "求职信",
        "salutation": "尊敬的招聘负责人：",
        "valediction": "此致 敬礼",
        "role_label": "职位",
        "type_label": "性质",
        "team_size_label": "团队规模",
        "proj_name_label": "项目名称",
        "period_label": "时间",
        "tech_stack_label": "技术栈",
        "outcomes_label": "成果",
        "remarks_label": "备注",
        "cert_exam_label": "证书/考试",
        "generated_at": "制作日期",
        "page_x_of_y": "第 {x} 页 / 共 {y} 页",
        "year": "年",
        "month": "月",
        "photo": "照片",
        "contact_alt": "联系方式 (备用)",
        "same_as_above": "同上",
        "entry": "入学",
        "graduation": "毕业",
        "as_of": "至今",
        "male": "男",
        "female": "女",
        "end_of_doc": "以上",
        "rirekisho_title": "履 歴 書",
        "shokumu_title": "職務経歴书",
        "phonetic": "ふりがな",
        "name_label": "氏　名",
        "as_of": "至今",
        "entry": "入学",
        "graduation": "毕业",
        "joining": "入社",
        "resignation": "退社",
        "self_pr_label": "自我介绍",
        "commute_time_label": "通勤时间",
        "dependents_label": "扶养家族",
        "spouse_label": "配偶",
        "spouse_dependency_label": "配偶扶养义务",
        "desired_conditions_label": "本人希望",
        "instructions_label": "注意事项",
        "same_as_above": "同上",
        "contact_alt_label": "紧急联系方式",
        "nationality_default": "印度",
        "wechat": "微信号",
        "photo_alt": "证件照",
        "photo_placeholder": "证件照 (28x36mm)",
        "category_label": "类别",
        "skills_tools_label": "技能 / 工具",
        "proficiency_label": "熟练度",
        "proficient_label": "熟练",
        "job_duties_label": "职责",
        "achievements_label": "业绩",
        "year_char": "年",
        "month_char": "月",
        "present": "至今",
        "writing_status": "撰写中",
        "cert_pending": "证书获取中",
        "hobbies": "兴趣爱好",
        "gpa_label": "GPA",
        "cl_growth": "成长背景",
        "cl_strengths": "性格特点",
        "cl_motivation": "求职动机",
        "cl_goals": "职业规划"
    }
}

TRANSLATION_PROMPT = """
You are a professional resume translator.

Rules:
1. Translate ONLY what is given.
2. Do NOT add or remove any information.
3. Keep all numbers, percentages, and metrics EXACTLY as they are (e.g., 94% stays 94%, 10k+ stays 10k+).
4. Keep company names in English (e.g., 'Logixbuilt Infotech' stays as is).
5. Keep technical terms in English (e.g., 'FastAPI', 'PostgreSQL', 'CNN' stays as is).
6. Translate ONLY natural language sentences.
7. Maintain a professional, sophisticated business tone.
8. Target language: {target_lang}
9. Return ONLY the translation, nothing else. No introductions or explanations.

Text to translate:
{text}
"""

import json
from typing import List, Dict

BATCH_TRANSLATION_PROMPT = """
You are a professional resume translator.

Rules:
1. Translate or REWRITE the following list of items to {target_lang}.
2. STRICT RULE: DO NOT translate technical terms, programming languages, or software names (e.g., Python, FastAPI, TensorFlow, PostgreSQL, REST API, ECG, ResNet). Keep them in English.
3. For Japan: Use business-appropriate Keigo. For China/Korea: Use formal, high-impact language.
4. Return ONLY a valid JSON array of objects, each containing "index" and "translation".
5. Return ONLY the JSON, no other text.

Items:
{items_json}
"""

SYNTHESIS_PROMPT = """
You are a professional resume consultant specializing in cultural adaptation for {target_lang_name}.

Task:
Rewrite the following resume snippet (in English) to be more appealing to recruiters in {target_lang_name}.

Rules:
1. DO NOT just translate. REWRITE the content to fit the cultural professional standards of that region.
2. REGION AWARENESS: If the text mentions "Japan" or "Japanese" but the target region is China or Korea, SWAP it for the correct country/language (e.g., "contributing to China's AI ecosystem" or "studying Korean"). If the target is International, use neutral global language.
3. Tone: Highly professional, formal, and achievement-oriented.
4. For Japan: Use business-appropriate Keigo. Emphasize team collaboration and stability.
5. For China: Emphasize high-impact metrics and certifications.
6. For South Korea: Use formal tone and specify project roles.
7. STRICT RULE: Keep technical terms (FastAPI, Python, CNN, etc.) in English.
8. Return ONLY the rewritten text in {target_lang_name}, nothing else.

Section context: {field_name}
Original English text:
{text}
"""

async def synthesize_text(text: str, target_lang: str, field_name: str = "generic") -> str:
    """Synthesizes and adapts text for a specific culture using Groq."""
    if not text or target_lang == "en":
        return text

    lang_name = {
        "ko": "Korean",
        "ja": "Japanese",
        "zh": "Chinese",
    }.get(target_lang, "English")

    prompt = SYNTHESIS_PROMPT.format(
        target_lang_name=lang_name,
        field_name=field_name,
        text=text
    )
    
    try:
        synthesized = await call_groq(prompt)
        synthesized = synthesized.strip()
        
        # Save to Cache as verified because this was a deliberate synthesis request
        save_translation(field_name, target_lang, text, synthesized, is_verified=True)
        
        return synthesized
    except Exception as e:
        print(f"Synthesis error: {e}")
        return text # Fallback to original English

async def translate_text(text: str, target_lang: str, field_name: str = "generic") -> str:
    """Translates text using Groq with SQLite caching."""
    if not text:
        return text
    
    # Normally skip English, unless the source is Japanese and we want English
    if target_lang == "en" and not contains_japanese(text):
        return text

    # 1. Check Cache
    cached = get_cached_translation(field_name, target_lang, text)
    if cached:
        return cached[0] # translated_text

    # 2. Call AI
    lang_name = {
        "ko": "Korean",
        "ja": "Japanese",
        "zh": "Chinese",
        "de": "German",
        "fr": "French",
        "en": "English"
    }.get(target_lang, "English")

    prompt = TRANSLATION_PROMPT.format(target_lang=lang_name, text=text)
    
    try:
        translated = await call_groq(prompt)
        translated = translated.strip()
        
        # 3. Save to Cache (Mark as unverified initially)
        save_translation(field_name, target_lang, text, translated, is_verified=False)
        
        return translated
    except Exception as e:
        print(f"Translation error: {e}")
        return text # Fallback to original English

async def translate_batch(items: List[Dict[str, str]], target_lang: str) -> List[str]:
    """
    Translates multiple strings in a single API call to avoid rate limits.
    items: List of {"text": "...", "field_name": "..."}
    """
    if not items:
        return []
    
    # Normally skip English, but if all items are already English, we can skip.
    # If any item contains Japanese, we might need to translate even to 'en'.
    if target_lang == "en":
        needs_translation = any(contains_japanese(item["text"]) for item in items)
        if not needs_translation:
            return [item["text"] for item in items]

    results = [None] * len(items)
    to_translate = [] # list of (original_index, item)

    # 1. Check Cache for each
    for i, item in enumerate(items):
        text = item["text"]
        field = item["field_name"]
        if not text:
            results[i] = ""
            continue
            
        cached = get_cached_translation(field, target_lang, text)
        if cached:
            results[i] = cached[0]
        else:
            to_translate.append((i, item))

    if not to_translate:
        return results

    # 2. Call AI in batches of 15 (to be safe with context and RPM)
    lang_name = {"ko": "Korean", "ja": "Japanese", "zh": "Chinese", "en": "English"}.get(target_lang, "English")
    
    # Process in chunks of 15
    for start_idx in range(0, len(to_translate), 15):
        chunk = to_translate[start_idx : start_idx + 15]
        
        chunk_data = [{"index": idx, "text": item["text"]} for idx, item in chunk]
        prompt = BATCH_TRANSLATION_PROMPT.format(
            target_lang=lang_name, 
            items_json=json.dumps(chunk_data, ensure_ascii=False)
        )
        
        try:
            response = await call_groq(prompt)
            # Clean response if AI adds markdown blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            translations = json.loads(response.strip())
            
            for t in translations:
                orig_idx = t["index"]
                translated_text = t["translation"]
                
                # Find the field name for this index
                field_name = next(item["field_name"] for idx, item in chunk if idx == orig_idx)
                orig_text = next(item["text"] for idx, item in chunk if idx == orig_idx)
                
                results[orig_idx] = translated_text
                # 3. Save to Cache
                save_translation(field_name, target_lang, orig_text, translated_text, is_verified=False)
        except Exception as e:
            print(f"Batch translation error for chunk {start_idx}: {e}")
            # Fallback for this chunk
            for idx, item in chunk:
                if results[idx] is None:
                    results[idx] = item["text"]

    # Fill any remaining Nones (shouldn't happen)
    return [r if r is not None else items[i]["text"] for i, r in enumerate(results)]

def get_labels(lang: str):
    """Returns the labels dictionary for the target language."""
    return LABELS.get(lang, LABELS["en"])

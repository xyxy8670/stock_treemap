import streamlit as st
import pandas as pd
import calendar
import datetime
import os
import requests
import matplotlib.font_manager as fm
from io import BytesIO
import platform

# 페이지 설정
st.set_page_config(page_title="청약일정 및 상장일정 달력", layout="wide")
st.title("청약일정 및 상장일정 달력")

# 세션 상태 초기화
if 'events' not in st.session_state:
    st.session_state.events = []
if 'filter_year' not in st.session_state:
    st.session_state.filter_year = datetime.date.today().year
if 'filter_month' not in st.session_state:
    st.session_state.filter_month = datetime.date.today().month

# 사이드바 - 날짜 선택
st.sidebar.header("달력 설정")
today = datetime.date.today()
selected_year = st.sidebar.selectbox("연도", list(range(today.year - 1, today.year + 3)), index=1)
selected_month = st.sidebar.selectbox("월", list(range(1, 13)), index=today.month - 1)

st.session_state.filter_year = selected_year
st.session_state.filter_month = selected_month

# 엑셀 파일 형식 안내
st.sidebar.header("엑셀 파일 형식 안내")
st.sidebar.info("""
엑셀 파일은 다음 컬럼을 포함해야 합니다:
- 종목명: 주식 종목명
- 일정유형: '청약' 또는 '상장'
- 시작일: YYYY-MM-DD 형식 (예: 2025-05-15)
- 종료일: YYYY-MM-DD 형식 (청약일정에만 필요)
""")

# 엑셀 파일 업로드
st.sidebar.header("엑셀 파일 업로드")
uploaded_file = st.sidebar.file_uploader("엑셀 파일을 업로드하세요 (.xlsx)", type=["xlsx"])

if uploaded_file is not None:
    try:
        df_upload = pd.read_excel(uploaded_file)
        # 필수 컬럼 확인
        required_columns = ['종목명', '일정유형', '시작일']
        missing_columns = [col for col in required_columns if col not in df_upload.columns]

        if missing_columns:
            st.sidebar.error(f"엑셀 파일에 필요한 컬럼이 없습니다: {', '.join(missing_columns)}")
        else:
            events = []
            for _, row in df_upload.iterrows():
                event = {
                    '종목명': row['종목명'],
                    '일정유형': row['일정유형'],
                    '시작일': pd.to_datetime(row['시작일']).date() if pd.notna(row['시작일']) else None
                }

                # 청약일정인 경우 종료일 필요
                if row['일정유형'] == '청약':
                    if '종료일' in df_upload.columns and pd.notna(row['종료일']):
                        event['종료일'] = pd.to_datetime(row['종료일']).date()
                    else:
                        # 종료일이 없는 경우 시작일과 동일하게 설정
                        event['종료일'] = event['시작일']

                # 상장일정인 경우 종료일은 시작일과 동일
                elif row['일정유형'] == '상장':
                    event['종료일'] = event['시작일']

                # 유효한 이벤트만 추가
                if event['시작일'] is not None:
                    events.append(event)

            st.session_state.events = events
            st.sidebar.success(f"{len(events)}개의 일정을 불러왔습니다.")

    except Exception as e:
        st.sidebar.error(f"엑셀 파일을 읽는 중 오류 발생: {str(e)}")

# 사이드바 - 일정 수동 추가
st.sidebar.header("일정 수동 추가")
event_type = st.sidebar.selectbox("일정 유형", ["청약", "상장"])
event_name = st.sidebar.text_input("종목명")
event_start_date = st.sidebar.date_input("시작일", today)

# 청약일정인 경우에만 종료일 입력 필드 표시
event_end_date = None
if event_type == "청약":
    event_end_date = st.sidebar.date_input("종료일", today)

if st.sidebar.button("일정 추가"):
    if event_name:
        new_event = {
            '종목명': event_name,
            '일정유형': event_type,
            '시작일': event_start_date
        }

        if event_type == "청약":
            new_event['종료일'] = event_end_date
        else:
            new_event['종료일'] = event_start_date

        st.session_state.events.append(new_event)
        st.sidebar.success(f"{event_name} {event_type} 일정이 추가되었습니다.")

# 전체 삭제 버튼
if st.sidebar.button("전체 일정 삭제"):
    st.session_state.events = []
    st.sidebar.success("모든 일정이 삭제되었습니다.")

# 샘플 데이터 추가 버튼
if st.sidebar.button("샘플 데이터 추가"):
    sample_events = [
        {
            '종목명': '넘버원',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 7),
            '종료일': datetime.date(selected_year, selected_month, 10)
        },
        {
            '종목명': '이앤드시스템',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 7),
            '종료일': datetime.date(selected_year, selected_month, 9)
        },
        {
            '종목명': '바이오비츄',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 8),
            '종료일': datetime.date(selected_year, selected_month, 10)
        },
        {
            '종목명': '닥터로보틱스',
            '일정유형': '상장',
            '시작일': datetime.date(selected_year, selected_month, 8),
            '종료일': datetime.date(selected_year, selected_month, 8)
        },
        {
            '종목명': '관리테라피',
            '일정유형': '상장',
            '시작일': datetime.date(selected_year, selected_month, 9),
            '종료일': datetime.date(selected_year, selected_month, 9)
        },
        {
            '종목명': '차타핀테크',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 11),
            '종료일': datetime.date(selected_year, selected_month, 15)
        },
        {
            '종목명': '롯데글로벌',
            '일정유형': '상장',
            '시작일': datetime.date(selected_year, selected_month, 16),
            '종료일': datetime.date(selected_year, selected_month, 16)
        },
        {
            '종목명': '인투셀',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 14),
            '종료일': datetime.date(selected_year, selected_month, 15)
        },
        {
            '종목명': '파워원',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 14),
            '종료일': datetime.date(selected_year, selected_month, 16)
        },
        {
            '종목명': '롯데개발',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 12),
            '종료일': datetime.date(selected_year, selected_month, 13)
        },
        {
            '종목명': '롯데액셀러레이터',
            '일정유형': '상장',
            '시작일': datetime.date(selected_year, selected_month, 12),
            '종료일': datetime.date(selected_year, selected_month, 12)
        },
        {
            '종목명': '키스앤16호',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 19),
            '종료일': datetime.date(selected_year, selected_month, 20)
        },
        {
            '종목명': '이앤드시스템',
            '일정유형': '상장',
            '시작일': datetime.date(selected_year, selected_month, 19),
            '종료일': datetime.date(selected_year, selected_month, 19)
        },
        {
            '종목명': '제네시스글로벌',
            '일정유형': '상장',
            '시작일': datetime.date(selected_year, selected_month, 21),
            '종료일': datetime.date(selected_year, selected_month, 21)
        },
        {
            '종목명': '키스트론',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 22),
            '종료일': datetime.date(selected_year, selected_month, 23)
        },
        {
            '종목명': '몰바글로벌',
            '일정유형': '상장',
            '시작일': datetime.date(selected_year, selected_month, 22),
            '종료일': datetime.date(selected_year, selected_month, 22)
        },
        {
            '종목명': '정크루즈',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 27),
            '종료일': datetime.date(selected_year, selected_month, 28)
        },
        {
            '종목명': '영진통',
            '일정유형': '청약',
            '시작일': datetime.date(selected_year, selected_month, 29),
            '종료일': datetime.date(selected_year, selected_month, 30)
        }
    ]
    st.session_state.events = sample_events
    st.sidebar.success("샘플 데이터를 추가했습니다.")


# HTML로 직접 달력 그리기 함수
def create_html_calendar(year, month, events):
    # 달력 데이터 가져오기
    cal = calendar.Calendar(firstweekday=6)  # 일요일부터 시작
    month_days = cal.monthdayscalendar(year, month)

    # 월 이름
    month_names = ['1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월']
    month_name = month_names[month - 1]

    # 요일 이름
    weekdays = ['일', '월', '화', '수', '목', '금', '토']

    # 이벤트 관리를 위한 데이터 구조
    # 1. 날짜별 이벤트 리스트
    date_events = {}

    # 2. 이벤트별 정보 (위치, 종류, 등)
    event_info = {}

    # 각 날짜에서 사용 중인 슬롯 수 추적
    date_slots = {}

    # 이벤트 정렬 및 슬롯 할당
    sorted_events = sorted(events, key=lambda e: (e['시작일'], -(e['종료일'] - e['시작일']).days))

    # 각 이벤트의 슬롯 할당
    for event in sorted_events:
        event_id = id(event)
        start_date = event['시작일']
        end_date = event['종료일']

        # 이 이벤트가 표시되는 날짜들
        event_dates = []
        current_date = start_date
        while current_date <= end_date:
            if current_date.year == year and current_date.month == month:
                event_dates.append(current_date.day)
            current_date += datetime.timedelta(days=1)

        if not event_dates:  # 이 월에 표시되는 날짜가 없으면 건너뛰기
            continue

        # 이 이벤트의 슬롯 결정
        slot = 0
        slots_in_use = set()

        # 이 이벤트의 날짜들에 이미 사용 중인 슬롯 확인
        for day in event_dates:
            if day in date_slots:
                slots_in_use.update(date_slots[day])

        # 사용 가능한 가장 낮은 슬롯 찾기
        while slot in slots_in_use:
            slot += 1

        # 이벤트 정보 저장
        event_info[event_id] = {
            'event': event,
            'slot': slot,
            'dates': event_dates
        }

        # 날짜별 이벤트 및 슬롯 정보 업데이트
        for day in event_dates:
            if day not in date_events:
                date_events[day] = []
            date_events[day].append(event_id)

            if day not in date_slots:
                date_slots[day] = set()
            date_slots[day].add(slot)

    # 각 날짜에서 최대 슬롯 수 계산
    max_slots = max([len(slots) for slots in date_slots.values()], default=0)

    # HTML 시작 - CSS 개선
    html = f"""
    <style>
        .calendar-container {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            max-width: 100%;
            margin: 0 auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
        }}
        .calendar-title {{
            text-align: center;
            padding: 15px;
            font-size: 24px;
            font-weight: bold;
            background-color: #f8f9fa;
            border-bottom: 1px solid #ddd;
        }}
        .calendar-table {{
            width: 100%;
            border-collapse: collapse;
            border-spacing: 0;
        }}
        .calendar-header {{
            background-color: #f8f9fa;
            text-align: center;
            padding: 10px;
            font-weight: bold;
            border: 1px solid #ddd;
        }}
        .day-cell {{
            vertical-align: top;
            border: 1px solid #ddd;
            height: 120px;
            width: 14.28%;
            padding: 5px;
            position: relative;
        }}
        .other-month {{
            background-color: #f5f5f5;
        }}
        .day-number {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 25px;
            display: block;
        }}
        .sunday .day-number {{
            color: #e74c3c;
        }}
        .saturday .day-number {{
            color: #3498db;
        }}
        .event-container {{
            margin-top: 2px;
            position: relative;
            height: 22px;
        }}
        .event {{
            position: absolute;
            left: 0;
            right: 0;
            height: 20px;
            line-height: 20px;
            padding: 0 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            color: white;
            font-weight: bold;
            font-size: 12px;
            border-radius: 0;
        }}
        /* 특별히 개선된 이벤트 스타일 - 연속성을 위한 마진 제거 */
        .event-청약 {{
            background-color: #5DA5DA;
        }}
        .event-상장 {{
            background-color: #FAA43A;
        }}
        .event-start {{
            border-top-left-radius: 4px;
            border-bottom-left-radius: 4px;
            margin-left: 1px; /* 시작 부분 살짝 들여쓰기 */
        }}
        .event-end {{
            border-top-right-radius: 4px;
            border-bottom-right-radius: 4px;
            margin-right: 1px; /* 끝 부분 살짝 들여쓰기 */
        }}
        /* 이벤트 사이에 간격이 없도록 하는 스타일 */
        .event-container .event {{
            margin-right: 0 !important; 
            margin-left: 0 !important;
            border-left: none !important;
            border-right: none !important;
        }}
        /* 테이블 셀 간 간격 제거 */
        .calendar-table td {{
            padding: 0 !important;
        }}
        /* 이벤트가 셀 경계를 넘어가도록 */
        .day-cell {{
            overflow: visible !important;
        }}
        /* 이벤트 컨테이너 관련 수정 */
        .event-row-container {{
            position: relative;
            height: 22px;
            overflow: visible;
        }}
    </style>

    <div class="calendar-container">
        <div class="calendar-title">{year}년 {month_name} 청약/상장 일정</div>
        <table class="calendar-table">
            <thead>
                <tr>
    """

    # 요일 헤더 추가
    for day_name in weekdays:
        html += f'<th class="calendar-header">{day_name}</th>'

    html += """
                </tr>
            </thead>
            <tbody>
    """

    # 날짜 그리드 생성
    for week_idx, week in enumerate(month_days):
        html += "<tr>"

        for day_idx, day in enumerate(week):
            # 셀 클래스 결정
            cell_class = ""
            if day == 0:
                cell_class = "other-month"
            elif day_idx == 0:  # 일요일
                cell_class = "sunday"
            elif day_idx == 6:  # 토요일
                cell_class = "saturday"

            html += f'<td class="day-cell {cell_class}">'

            if day != 0:  # 이번 달의 날짜만 표시
                html += f'<span class="day-number">{day}</span>'

                # 이 날짜의 모든 이벤트 슬롯에 대한 컨테이너 생성
                for slot in range(max_slots):
                    html += f'<div class="event-container" data-slot="{slot}">'

                    # 이 슬롯에 이벤트가 있는지 확인
                    event_found = False
                    if day in date_events:
                        for event_id in date_events[day]:
                            info = event_info[event_id]
                            if info['slot'] == slot:
                                event = info['event']
                                dates = info['dates']

                                # 이벤트 클래스 결정
                                is_start = day == dates[0]
                                is_end = day == dates[-1]
                                event_class = f"event event-{event['일정유형']}"

                                if is_start:
                                    event_class += " event-start"
                                if is_end:
                                    event_class += " event-end"

                                # 이벤트 내용 (시작일에만 텍스트 표시)
                                content = event['종목명'] if is_start else "&nbsp;"

                                html += f'<div class="{event_class}" data-event-id="{event_id}">{content}</div>'
                                event_found = True
                                break

                    html += '</div>'

            html += '</td>'

        html += "</tr>"

    # HTML 종료
    html += """
            </tbody>
        </table>
    </div>

    <script>
    // 이벤트 바가 셀 경계를 넘어 연속되도록 하는 자바스크립트
    document.addEventListener('DOMContentLoaded', function() {
        // 이벤트 연속성 확보를 위한 마진 제거
        const cells = document.querySelectorAll('.day-cell');
        cells.forEach(cell => {
            cell.style.position = 'relative';
            cell.style.padding = '0';
        });

        // 이벤트 바의 width를 100%+로 조정하여 경계를 넘어가도록 함
        const events = document.querySelectorAll('.event:not(.event-start):not(.event-end)');
        events.forEach(event => {
            event.style.width = 'calc(100% + 2px)';
            event.style.left = '-1px';
        });

        // 시작 이벤트는 오른쪽으로만 확장
        const startEvents = document.querySelectorAll('.event.event-start:not(.event-end)');
        startEvents.forEach(event => {
            event.style.width = 'calc(100% + 1px)';
        });

        // 끝 이벤트는 왼쪽으로만 확장
        const endEvents = document.querySelectorAll('.event.event-end:not(.event-start)');
        endEvents.forEach(event => {
            event.style.width = 'calc(100% + 1px)';
            event.style.left = '-1px';
        });
    });
    </script>
    """

    return html


# 이벤트 목록 표시 (탭 형식으로 분리)
tab1, tab2 = st.tabs(["달력 보기", "일정 목록 편집"])

with tab1:
    # HTML로 달력 표시
    calendar_html = create_html_calendar(selected_year, selected_month, st.session_state.events)
    st.markdown(calendar_html, unsafe_allow_html=True)

    # 현재 월의 일정 목록 아래에 표시
    st.markdown("### 이번 달 일정")

    # 현재 월의 일정만 필터링
    current_month_events = [
        event for event in st.session_state.events
        if (event['시작일'].year == selected_year and event['시작일'].month == selected_month) or
           (event['종료일'].year == selected_year and event['종료일'].month == selected_month)
    ]

    # 날짜별로 정렬
    current_month_events.sort(key=lambda x: x['시작일'])

    # CSS 스타일 정의
    st.markdown("""
    <style>
    .event-card {
        padding: 12px;
        margin-bottom: 10px;
        border-radius: 8px;
        display: flex;
        align-items: center;
    }
    .event-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 10px;
    }
    .event-content {
        flex-grow: 1;
    }
    .event-title {
        font-weight: 500;
        margin-bottom: 4px;
    }
    .event-date {
        font-size: 12px;
        color: #666;
    }
    .event-type-청약 {
        background-color: #EBF5FB;
        border-left: 4px solid #5DA5DA;
    }
    .event-type-상장 {
        background-color: #FEF5E7;
        border-left: 4px solid #FAA43A;
    }
    </style>
    """, unsafe_allow_html=True)

    # 일정이 있는 경우에만 표시
    if current_month_events:
        for event in current_month_events:
            event_type = event['일정유형']
            dot_color = "#5DA5DA" if event_type == "청약" else "#FAA43A"

            # 날짜 포맷팅
            if event['시작일'] == event['종료일']:
                date_str = event['시작일'].strftime('%Y년 %m월 %d일')
            else:
                date_str = f"{event['시작일'].strftime('%Y년 %m월 %d일')} - {event['종료일'].strftime('%Y년 %m월 %d일')}"

            st.markdown(f"""
            <div class="event-card event-type-{event_type}">
                <div class="event-dot" style="background-color: {dot_color};"></div>
                <div class="event-content">
                    <div class="event-title">{event['종목명']} ({event_type})</div>
                    <div class="event-date">{date_str}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("이번 달 등록된 일정이 없습니다.")

with tab2:
    st.header("전체 일정 목록")
    if st.session_state.events:
        # 데이터프레임 생성
        df_events = pd.DataFrame(st.session_state.events)

        # 데이터 에디터로 표시
        edited_df = st.data_editor(
            df_events,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "시작일": st.column_config.DateColumn("시작일", format="YYYY-MM-DD"),
                "종료일": st.column_config.DateColumn("종료일", format="YYYY-MM-DD"),
                "일정유형": st.column_config.SelectboxColumn(
                    "일정유형", options=["청약", "상장"], required=True
                )
            },
            key="editable_events"
        )

        # 변경사항 적용
        new_events = edited_df.to_dict('records')
        st.session_state.events = new_events

        # 엑셀 내보내기 기능
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_events.to_excel(writer, index=False, sheet_name='일정')

        st.download_button(
            label="일정 엑셀 다운로드",
            data=excel_buffer.getvalue(),
            file_name="일정_데이터.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("일정을 추가하거나 엑셀 파일을 업로드하세요.")
# 푸터
st.write("---")
st.caption("© 2025 청약일정 및 상장일정 달력 | 모든 정보는 참고용으로만 제공됩니다.")
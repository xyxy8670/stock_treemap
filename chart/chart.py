import streamlit as st
import matplotlib.pyplot as plt
import squarify
import numpy as np
import matplotlib.font_manager as fm
import matplotlib.patches as patches
import pandas as pd
from io import BytesIO
import os
import requests
import tempfile
from matplotlib.colors import to_rgb, to_hex

# 페이지 설정
st.set_page_config(page_title="주식 테마 트리맵 생성기", layout="wide")
st.title("주식 테마 트리맵 생성기 (버전 1.1)")


# Pretendard 폰트 다운로드 및 설정
def setup_font():
    try:
        font_dir = os.path.join(os.getcwd(), 'fonts')
        os.makedirs(font_dir, exist_ok=True)
        font_path = os.path.join(font_dir, 'Pretendard-SemiBold.otf')

        if not os.path.exists(font_path):
            font_url = 'https://raw.githubusercontent.com/xyxy8670/stock_treemap/8c4363de7470242d6f04bdda2de16cd3454b70fa/chart/Pretendard-SemiBold.otf'
            try:
                response = requests.get(font_url)
                if response.status_code == 200:
                    with open(font_path, 'wb') as f:
                        f.write(response.content)
                    st.success(f"Pretendard 폰트를 다운로드했습니다: {font_path}")
                else:
                    st.warning(f"폰트 다운로드 실패 (상태 코드: {response.status_code}). 시스템 폰트를 사용합니다.")
                    return None
            except Exception as e:
                st.warning(f"폰트 다운로드 오류: {str(e)}")
                return None

        try:
            fm.fontManager.addfont(font_path)
            font_obj = fm.FontProperties(fname=font_path)
            plt.rcParams['font.family'] = font_obj.get_name()
            plt.rcParams['axes.unicode_minus'] = False
            return font_obj
        except Exception as e:
            st.warning(f"폰트 등록 오류: {str(e)}")
            return None
    except Exception as e:
        st.warning(f"폰트 설정 오류: {str(e)}")
        return None


font_prop = setup_font()

# 엑셀 파일 업로드 (테마와 퍼센테이지 컬럼 인식)
st.sidebar.header("엑셀 파일 업로드")
uploaded_file = st.sidebar.file_uploader("엑셀 파일을 업로드하세요 (.xlsx)", type=["xlsx"])
if uploaded_file is not None:
    try:
        df_upload = pd.read_excel(uploaded_file)
        if "테마" in df_upload.columns and "퍼센테이지" in df_upload.columns:
            new_data = dict(zip(df_upload["테마"], df_upload["퍼센테이지"]))
            st.session_state.theme_data = new_data
            st.sidebar.success("엑셀 파일의 데이터를 불러왔습니다.")
        else:
            st.sidebar.error("엑셀 파일에 '테마'와 '퍼센테이지' 컬럼이 존재해야 합니다.")
    except Exception as e:
        st.sidebar.error(f"엑셀 파일을 읽는 중 오류 발생: {str(e)}")

# 사이드바 - 데이터 입력
st.sidebar.header("테마 데이터 입력")
theme_name = st.sidebar.text_input("테마 이름")
theme_value = st.sidebar.number_input("상승률(%)", min_value=0.0, format="%.2f")

if 'theme_data' not in st.session_state:
    st.session_state.theme_data = {}

if st.sidebar.button("데이터 추가"):
    if theme_name and theme_value:
        st.session_state.theme_data[theme_name] = theme_value
        st.sidebar.success(f"테마 '{theme_name}'이(가) {theme_value}% 상승률로 추가되었습니다.")

# 시각화 옵션
st.sidebar.header("시각화 옵션")
color_option = st.sidebar.selectbox("색상 계열", ["Reds", "Greens", "Blues", "Purples", "Oranges"])
# 내부 색상 코드 입력 (비워두면 colormap 사용)
custom_color_code = st.sidebar.text_input("내부 색상 코드 (예: #ff0000)", value="")
title_text = st.sidebar.text_input("제목", "테마별 주식 상승률 트리맵")
theme_font_size = st.sidebar.slider("테마명 폰트 크기", 8, 24, 14)
value_font_size = st.sidebar.slider("상승률 폰트 크기", 8, 24, 16)

# 워터마크 옵션
watermark_enabled = st.sidebar.checkbox("워터마크 추가", True)
watermark_text = st.sidebar.text_input("워터마크 텍스트", "플스포")
watermark_opacity = st.sidebar.slider("워터마크 투명도", 0.0, 1.0, 0.3)
watermark_size = st.sidebar.slider("워터마크 크기", 20, 100, 50)

# 현재 데이터 편집 (data_editor)
st.sidebar.header("현재 데이터 (편집 가능)")
df_data = {
    '테마': list(st.session_state.theme_data.keys()),
    '상승률(%)': list(st.session_state.theme_data.values())
}
df = pd.DataFrame(df_data)
edited_df = st.sidebar.data_editor(
    df,
    num_rows="dynamic",
    use_container_width=True,
    key="editable_data"
)

# 즉시 수정 내용을 session_state에 반영
new_data = {}
for idx, row in edited_df.iterrows():
    theme = str(row['테마']).strip()
    if theme:
        try:
            val = float(row['상승률(%)'])
        except:
            val = 0.0
        new_data[theme] = val
st.session_state.theme_data = new_data

# 트리맵 미리보기
st.header("트리맵 미리보기")
if st.session_state.theme_data:
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        # 상승률 기준 내림차순 정렬
        sorted_data = sorted(st.session_state.theme_data.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_data]
        values = [item[1] for item in sorted_data]
        sizes = values

        max_val = max(values) if values else 1
        min_val = min(values) if values else 0
        normalized_values = [
            (val - min_val) / (max_val - min_val) if max_val > min_val else 0.5
            for val in values
        ]

        # 내부 색상 지정:
        # custom_color_code가 입력되면, 최고 상승률 항목은 원본 색상, 나머지는 어두워지도록 선형 보간
        if custom_color_code:
            base_rgb = to_rgb(custom_color_code)
            dark_factor = 0.7  # 최저값일 때 밝기 배율 (0~1)
            colors = []
            for n in normalized_values:
                factor = dark_factor + (1 - dark_factor) * n
                adjusted_rgb = tuple(comp * factor for comp in base_rgb)
                colors.append(to_hex(adjusted_rgb))
        else:
            cmap = plt.cm.get_cmap(color_option)
            colors = [cmap(0.5 + 0.5 * n) for n in normalized_values]

        if values:
            norm_sizes = [size / sum(sizes) for size in sizes]
            rects = squarify.squarify(norm_sizes, 0, 0, 1, 1)
            for i, rect in enumerate(rects):
                x, y, dx, dy = rect['x'], rect['y'], rect['dx'], rect['dy']
                ax.add_patch(
                    patches.Rectangle(
                        (x, y), dx, dy,
                        facecolor=colors[i],
                        edgecolor='white',
                        linewidth=2,
                        alpha=0.8
                    )
                )
                if font_prop is not None:
                    ax.text(
                        x + dx / 2,
                        y + dy / 2 - 0.02,
                        f"{labels[i]}",
                        fontproperties=font_prop,
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=theme_font_size,
                        fontweight='bold',
                        color='white'
                    )
                    ax.text(
                        x + dx / 2,
                        y + dy / 2 + 0.04,
                        f"{values[i]}%",
                        fontproperties=font_prop,
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=value_font_size,
                        fontweight='bold',
                        color='white'
                    )
                else:
                    ax.text(
                        x + dx / 2,
                        y + dy / 2 - 0.02,
                        f"{labels[i]}",
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=theme_font_size,
                        fontweight='bold',
                        color='white'
                    )
                    ax.text(
                        x + dx / 2,
                        y + dy / 2 + 0.04,
                        f"{values[i]}%",
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize=value_font_size,
                        fontweight='bold',
                        color='white'
                    )

            if watermark_enabled:
                if font_prop is not None:
                    fig.text(
                        0.5, 0.5, watermark_text,
                        fontproperties=font_prop,
                        fontsize=watermark_size,
                        color='white',
                        ha='center',
                        va='center',
                        alpha=watermark_opacity,
                        fontweight='bold',
                        rotation=0
                    )
                else:
                    fig.text(
                        0.5, 0.5, watermark_text,
                        fontsize=watermark_size,
                        color='white',
                        ha='center',
                        va='center',
                        alpha=watermark_opacity,
                        fontweight='bold',
                        rotation=0
                    )

        if font_prop is not None:
            fig.suptitle(title_text, fontproperties=font_prop, fontsize=18)
        else:
            fig.suptitle(title_text, fontsize=18)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        st.pyplot(fig)

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
        st.download_button(
            label="트리맵 이미지 다운로드",
            data=buf.getvalue(),
            file_name="treemap.png",
            mime="image/png"
        )
    except Exception as e:
        st.error(f"트리맵 생성 중 오류 발생: {str(e)}")
        st.exception(e)
else:
    st.info("트리맵을 생성하려면 데이터를 추가하거나 샘플 데이터를 불러오세요.")
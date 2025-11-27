import streamlit as st
from openai import OpenAI
import anthropic  # 对于Claude
from rdkit import Chem
from rdkit.Chem import Draw
import base64
from io import BytesIO

st.set_page_config(page_title="SeeChem - 有机化学AI助手", layout="wide")
st.title("🧪 SeeChem: 有机化学可视化助手")

# 侧边栏配置
api_key = st.sidebar.text_input("API Key (OpenAI或Claude)", type="password")
model_choice = st.sidebar.selectbox("选择AI模型", ["GPT-4o-mini (OpenAI)", "Claude-3.5-Sonnet (Anthropic)"])

user_question = st.text_area("输入你的有机化学问题（支持中文）", height=150, placeholder="例如：解释Diels-Alder反应的机制，并画出结构式。")

if st.button("🚀 生成答案") and user_question and api_key:
    with st.spinner("AI思考中..."):
        # 构建提示
        prompt = f"""
        你是一个专业的有机化学老师。用户问题：{user_question}
        用中文详细解释，并提取所有分子用SMILES表示。
        输出格式（严格JSON，便于解析）：
        {{"text": "详细解释文本",
         "smiles_list": [{{"name": "反应物1", "smiles": "CC(=O)O"}}, {{"name": "产物1", "smiles": "C"}}]}}
        只输出JSON，无其他文字。
        """

        try:
            if "GPT" in model_choice:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                json_response = response.choices[0].message.content
            else:  # Claude
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                json_response = response.content[0].text

            import json
            data = json.loads(json_response)

            st.markdown("### 解释：")
            st.write(data["text"])

            st.markdown("### 分子结构：")
            cols = st.columns(3)  # 3列显示图像
            for i, mol in enumerate(data["smiles_list"]):
                try:
                    rd_mol = Chem.MolFromSmiles(mol["smiles"])
                    img = Draw.MolToImage(rd_mol, size=(300, 300))
                    buffered = BytesIO()
                    img.save(buffered, format="PNG")
                    img_str = base64.b64encode(buffered.getvalue()).decode()
                    with cols[i % 3]:
                        st.image(f"data:image/png;base64,{img_str}", caption=mol["name"], width=250)
                except Exception as e:
                    st.error(f"无法绘制 {mol['name']}: {e}")

            # 简单反应示例（可选扩展）
            if len(data["smiles_list"]) >= 2:
                st.markdown("### 示例反应示意图（带箭头）：")
                rxn = Chem.ReactionFromSmarts(f"{data['smiles_list'][0]['smiles']}>>{data['smiles_list'][1]['smiles']}")
                rxn_img = Draw.ReactionToImage(rxn)
                buffered = BytesIO()
                rxn_img.save(buffered, format="PNG")
                rxn_str = base64.b64encode(buffered.getvalue()).decode()
                st.image(f"data:image/png;base64,{rxn_str}", caption="反应路径")

        except Exception as e:
            st.error(f"出错了：{e}. 检查API key或模型。")

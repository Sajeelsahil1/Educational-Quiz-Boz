import google.generativeai as genai

genai.configure(api_key="AIzaSyDdNsf_7D3dIQY_2BiBkxADPS9ynGO9R1U")

print([m.name for m in genai.list_models()])

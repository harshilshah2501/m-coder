import json
import os

# Configuration
INPUT_FILE = 'comprehensive_evaluation_20260107_070227.json'
OUTPUT_FILE = 'evaluation_report_v16_1.html'

def create_html_report(json_path, output_path):
    if not os.path.exists(json_path):
        print(f"Error: File {json_path} not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get('results', [])

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Evaluation Results - v16_1</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1200px; margin: 0 auto; padding: 20px; background-color: #f4f7f6; }
            h1 { text-align: center; color: #2c3e50; }
            .test-case { background: white; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 40px; overflow: hidden; border: 1px solid #ddd; }
            .header { background: #2c3e50; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; }
            .use-case { font-weight: bold; text-transform: uppercase; letter-spacing: 1px; font-size: 0.9em; background: #34495e; padding: 4px 10px; border-radius: 4px; }
            .content-grid { display: grid; grid-template-columns: 1fr; gap: 0; }
            .section { padding: 20px; border-bottom: 1px solid #eee; }
            .section-title { font-weight: bold; margin-bottom: 10px; color: #e67e22; text-transform: uppercase; font-size: 0.85em; border-left: 4px solid #e67e22; padding-left: 10px; }
            pre { background: #282c34; color: #abb2bf; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace; font-size: 0.9em; white-space: pre-wrap; word-break: break-all; }
            .expected { border-left-color: #27ae60; }
            .expected .section-title { color: #27ae60; border-left-color: #27ae60; }
            .model .section-title { color: #2980b9; border-left-color: #2980b9; }
        </style>
    </head>
    <body>
        <h1>Model Evaluation Report: v16_1</h1>
    """

    for i, item in enumerate(results):
        use_case = item.get('use_case', 'N/A')
        user_input = item.get('user_input', '')
        expected = item.get('expected_output', '')
        model_out = item.get('model_output', '')

        html_content += f"""
        <div class="test-case">
            <div class="header">
                <span>Sample #{i}</span>
                <span class="use-case">{use_case}</span>
            </div>
            <div class="content-grid">
                <div class="section">
                    <div class="section-title">User Input</div>
                    <pre>{user_input}</pre>
                </div>
                <div class="section expected">
                    <div class="section-title">Expected Output</div>
                    <pre>{expected}</pre>
                </div>
                <div class="section model">
                    <div class="section-title">Model Output</div>
                    <pre>{model_out}</pre>
                </div>
            </div>
        </div>
        """

    html_content += """
    </body>
    </html>
    """

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Success! Report generated: {output_path}")
    print("Open this file in your Chrome or Firefox browser to analyze.")

if __name__ == "__main__":
    create_html_report(INPUT_FILE, OUTPUT_FILE)
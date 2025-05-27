import os

# Thư mục chứa các file HTML cần sửa
html_folder = './'

# Chuỗi cần thay
old_path = 'assets/'
new_path = '/static/admin/assets/'

# Tìm và sửa tất cả các file .html trong thư mục admin
def fix_asset_paths(folder, old, new):
    updated = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if old in content:
                    content = content.replace(old, new)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    updated.append(filepath)
    return updated

if __name__ == '__main__':
    updated_files = fix_asset_paths(html_folder, old_path, new_path)
    if updated_files:
        print("✅ Đã sửa các file:")
        for f in updated_files:
            print(f"- {f}")
    else:
        print("⚠️ Không tìm thấy file nào cần sửa.")

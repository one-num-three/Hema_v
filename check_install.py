import os, subprocess

ppt_dir = r"F:\hema-fix\ppt-master"
print("=== ppt-master 安装状态 ===\n")

# 1. 仓库位置
print(f"📁 仓库位置: {ppt_dir}")
print(f"    存在: {os.path.isdir(ppt_dir)}")
print(f"    大小: {sum(os.path.getsize(os.path.join(dp,f)) for dp,dn,fn in os.walk(ppt_dir) for f in fn):,} bytes")

# 2. 核心文件
core_files = [
    r"skills\ppt-master\SKILL.md",
    r".env.example",
]
for f in core_files:
    path = os.path.join(ppt_dir, f)
    print(f"📄 {f}: {'✅' if os.path.exists(path) else '❌'}")

# 3. 脚本总数
scripts = [f for f in os.listdir(os.path.join(ppt_dir, r"skills\ppt-master\scripts")) if f.endswith(".py")]
print(f"\n🔧 脚本总数: {len(scripts)}")

# 4. python-pptx
try:
    import pptx
    print(f"📦 python-pptx 版本: {pptx.__version__}")
except:
    print("📦 python-pptx: ❌ 未安装")

# 5. 关键脚本
key_scripts = ["svg_to_pptx.py", "image_gen.py", "project_manager.py"]
for s in key_scripts:
    path = os.path.join(ppt_dir, r"skills\ppt-master\scripts", s)
    print(f"🧪 {s}: {'✅' if os.path.exists(path) else '❌'}")

# 6. Hermes skill
skill_path = os.path.expanduser(r"~\.hermes\skills\productivity\ppt-master\SKILL.md")
print(f"\n🎯 Hermes Skill: {'✅ 已创建' if os.path.exists(skill_path) else '❌ 未创建'}")

print("\n✅ 安装完成！")

import csv
import time
import requests
import json
import subprocess
import os

# 清除代理环境变量
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)

def fetch_ips(): 
    response = requests.get('https://ipdb.api.030101.xyz/?type=cfv4;proxy')

# 检查响应状态码
    if response.status_code == 200:
    # 将返回的IP保存为hero.txt
        with open('hero.txt', 'w') as file:
            file.write(response.text)
    else:
        print(f"请求失败，状态码：{response.status_code}")
    



# Part3.生成result.csv
def run_cloudflare_speedtest():
    print("测速并生成result.csv...")
    subprocess.run(["./hero.sh"], shell=True)

    print("测速完成，生成result.csv文件")

def get_ips():  # 读取result.csv文件中的IPs
    ips = []
    with open("result.csv", "r",encoding="utf-8") as csvfile:
        csvreader = csv.reader(csvfile)
        next(csvreader)  # skip header
        for row in csvreader:
            ips.append(row[0])
        return ips


# Part4.更新Cloudflare DNS记录
def load_config(): # 读取config.json文件
    with open("./config/config.json", "r", encoding="utf-8") as file:
        config = json.load(file)
        email = config.get("email")
        global_api_key = config.get("global_api_key")
        zone_id = config.get("zone_id")
        domains = config.get("domains")
        if not email or not global_api_key or not zone_id or not domains:
            print("错误: config.json文件中缺少必要的key！")
            exit()
    return email, global_api_key, zone_id, domains

def update_cloudflare_dns(email, global_api_key, zone_id, domains):
    print("更新Cloudflare DNS记录...")
    ips = get_ips()  # 读取result.csv文件中的IPs
    res_domains=domains.copy() #复制domains字典
    for idx, (domain, record_id) in enumerate(domains.items()):
        if idx >= len(ips):
            print(f"可用ip数量不足，截至域名: {domain}")
            #将剩余domains字典中的域名添加到not_updated_domains字典中
            break

        ip = ips[idx]
        print(f"Processing Domain[{idx + 1}] : {domain} with IP: {ip}")

        headers = {
            "X-Auth-Email": email,
            "X-Auth-Key": global_api_key,
            "Content-Type": "application/json"
        }
        data = {
            "type": "A",
            "name": domain,
            "content": ip,
            "ttl": 60,
            "proxied": False
        }

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
        response = requests.put(url, headers=headers, data=json.dumps(data))
        res_domains.pop(domain, None)  # 从domains字典中删除已更新的域名
        print(response.json())
    return res_domains  # 返回未更新的域名

def main():
    fetch_ips()
    print("中转节点下载完成，开始筛选...")
    run_cloudflare_speedtest()  # 生成result.csv文件

    email, global_api_key, zone_id, domains = load_config() # 读取config.json文件
    domains = update_cloudflare_dns(email, global_api_key, zone_id, domains)
    while domains:
        print("未更新的域名: ", domains)
        print("正在重新测速并更新...")
        run_cloudflare_speedtest()  # 生成result.csv文件
        domains = update_cloudflare_dns(email, global_api_key, zone_id, domains)
    


if __name__=="__main__":
    main()
    print("3秒后自动退出程序")
    time.sleep(3)
    

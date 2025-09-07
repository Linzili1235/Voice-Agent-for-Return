#!/usr/bin/env python3
# 退货流程演示脚本 - 演示完整的退货/退款流程
import requests
import json
import time
from typing import Dict, Any


class ReturnWorkflowDemo:
    """Demo class for return workflow."""
    
    def __init__(self, base_url: str = "http://localhost:8787"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def demo_amazon_return(self):
        """Demo Amazon return workflow."""
        print("🛒 Amazon 退货流程演示")
        print("=" * 50)
        
        # Step 1: Generate RMA email
        print("1. 生成 RMA 邮件...")
        email_request = {
            "vendor": "amazon",
            "order_id": "123-4567890-1234567",
            "item_sku": "B08N5WRWNW",
            "intent": "return",
            "reason": "damaged",
            "evidence_urls": ["https://example.com/photo1.jpg"],
            "contact_email": "customer@example.com"
        }
        
        response = self.session.post(
            f"{self.base_url}/tools/make_rma_email",
            json=email_request
        )
        
        if response.status_code == 200:
            email_data = response.json()
            print(f"   ✓ 邮件生成成功")
            print(f"   📧 收件人: {email_data['to_email']}")
            print(f"   📝 主题: {email_data['subject']}")
            print(f"   📄 正文长度: {len(email_data['body'])} 字符")
        else:
            print(f"   ✗ 邮件生成失败: {response.text}")
            return
        
        # Step 2: Send email
        print("\n2. 发送邮件...")
        send_request = {
            "to": email_data["to_email"],
            "subject": email_data["subject"],
            "body": email_data["body"],
            "idempotency_key": f"demo-{int(time.time())}"
        }
        
        response = self.session.post(
            f"{self.base_url}/tools/send_email",
            json=send_request
        )
        
        if response.status_code == 200:
            send_data = response.json()
            print(f"   ✓ 邮件发送成功")
            print(f"   📨 消息ID: {send_data['msg_id']}")
            msg_id = send_data['msg_id']
        else:
            print(f"   ✗ 邮件发送失败: {response.text}")
            return
        
        # Step 3: Log submission
        print("\n3. 记录提交...")
        log_request = {
            "vendor": "amazon",
            "order_id_last4": "4567",
            "intent": "return",
            "reason": "damaged",
            "msg_id": msg_id
        }
        
        response = self.session.post(
            f"{self.base_url}/tools/log_submission",
            json=log_request
        )
        
        if response.status_code == 200:
            print(f"   ✓ 提交记录成功")
        else:
            print(f"   ✗ 提交记录失败: {response.text}")
        
        # Step 4: Send confirmation SMS
        print("\n4. 发送确认短信...")
        sms_request = {
            "phone": "+1234567890",
            "text": f"您的退货申请已提交，参考号：{msg_id}。我们会在1-2个工作日内处理您的申请。"
        }
        
        response = self.session.post(
            f"{self.base_url}/tools/send_sms",
            json=sms_request
        )
        
        if response.status_code == 200:
            print(f"   ✓ 确认短信发送成功")
        else:
            print(f"   ✗ 确认短信发送失败: {response.text}")
        
        print("\n✅ Amazon 退货流程演示完成！")
    
    def demo_workflow_endpoint(self):
        """Demo workflow endpoint."""
        print("\n🔄 完整工作流端点演示")
        print("=" * 50)
        
        workflow_request = {
            "vendor": "walmart",
            "order_id": "WM123456789",
            "item_sku": "WM-SKU-123",
            "intent": "refund",
            "reason": "wrong_item",
            "evidence_urls": [],
            "contact_email": "user@example.com",
            "contact_phone": "+1987654321"
        }
        
        print("发送工作流请求...")
        response = self.session.post(
            f"{self.base_url}/workflow/return",
            json=workflow_request
        )
        
        if response.status_code == 200:
            workflow_data = response.json()
            print(f"   ✓ 工作流执行成功")
            print(f"   📊 状态: {workflow_data['status']}")
            print(f"   💬 消息: {workflow_data['message']}")
            print(f"   ⏱️  执行时间: {workflow_data['execution_time']:.2f} 秒")
            
            if workflow_data.get('data'):
                data = workflow_data['data']
                print(f"   📧 邮件发送: {'✓' if data.get('email_sent') else '✗'}")
                print(f"   📱 短信发送: {'✓' if data.get('sms_sent') else '✗'}")
                print(f"   📝 记录日志: {'✓' if data.get('logged') else '✗'}")
                if data.get('msg_id'):
                    print(f"   🆔 消息ID: {data['msg_id']}")
        else:
            print(f"   ✗ 工作流执行失败: {response.text}")
    
    def demo_policy_query(self):
        """Demo policy query."""
        print("\n📋 政策查询演示")
        print("=" * 50)
        
        # Query Amazon policy
        policy_request = {
            "vendor": "amazon"
        }
        
        response = self.session.post(
            f"{self.base_url}/workflow/policy",
            json=policy_request
        )
        
        if response.status_code == 200:
            policy_data = response.json()
            print(f"   📋 {policy_data['vendor'].title()} 政策:")
            for key, value in policy_data['policies'].items():
                print(f"      • {key}: {value}")
        else:
            print(f"   ✗ 政策查询失败: {response.text}")
    
    def demo_health_check(self):
        """Demo health check."""
        print("\n🏥 健康检查演示")
        print("=" * 50)
        
        response = self.session.get(f"{self.base_url}/health")
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"   ✓ 服务状态: {health_data['status']}")
            print(f"   📦 版本: {health_data['version']}")
        else:
            print(f"   ✗ 健康检查失败: {response.text}")
    
    def run_full_demo(self):
        """Run full demo."""
        print("🚀 退货/退款流程完整演示")
        print("=" * 60)
        
        try:
            # Check if server is running
            self.demo_health_check()
            
            # Demo individual tools
            self.demo_amazon_return()
            
            # Demo workflow endpoint
            self.demo_workflow_endpoint()
            
            # Demo policy query
            self.demo_policy_query()
            
            print("\n🎉 所有演示完成！")
            print("\n📚 API 文档: http://localhost:8787/docs")
            print("📊 指标监控: http://localhost:8787/metrics")
            
        except requests.exceptions.ConnectionError:
            print("❌ 无法连接到服务器")
            print("请确保服务器正在运行: python run_server.py")
        except Exception as e:
            print(f"❌ 演示过程中出现错误: {e}")


def main():
    """Main function."""
    demo = ReturnWorkflowDemo()
    demo.run_full_demo()


if __name__ == "__main__":
    main()


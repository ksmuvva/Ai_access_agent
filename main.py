"""
Main CLI Entry Point for AI Accessibility Testing Agent
Uses Google ADK hierarchical sub-agents pattern with A2A protocol support
"""

import click
import asyncio
import json
from typing import Optional
from adk_orchestrator import ADKAccessibilityOrchestrator
from utils.logger import setup_logger

logger = setup_logger(__name__)

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """AI Accessibility Testing Agent - WCAG 2.2 UK Compliance Testing"""
    pass

@cli.command()
@click.argument('url')
@click.option('--agents', '-a', multiple=True, 
              type=click.Choice(['keyboard-focus', 'color-contrast', 'all']),
              default=['all'],
              help='Specify which agents to run (now managed by ADK coordinator)')
@click.option('--output', '-o', type=str, default='accessibility_report.json',
              help='Output file for the accessibility report')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--wcag-level', type=click.Choice(['A', 'AA', 'AAA']), default='AA',
              help='WCAG compliance level')
@click.option('--enable-a2a', is_flag=True, help='Enable A2A protocol for remote agents')
def test(url: str, agents: tuple, output: str, verbose: bool, wcag_level: str, enable_a2a: bool):
    """Test accessibility using ADK hierarchical agents with A2A protocol support"""
    if verbose:
        logger.setLevel(10)  # DEBUG level
    
    click.echo(f"🤖 Starting ADK Accessibility Testing for: {url}")
    click.echo(f"📋 WCAG Level: {wcag_level} | A2A Protocol: {'Enabled' if enable_a2a else 'Disabled'}")
    
    async def run_test():
        try:
            # Configure test options
            test_options = {
                'wcag_version': '2.2',
                'compliance_level': wcag_level,
                'include_remote_agents': enable_a2a,
                'agent_filter': list(agents) if 'all' not in agents else None            }
            
            # Initialize ADK orchestrator
            orchestrator = ADKAccessibilityOrchestrator()
            
            # Run ADK-based accessibility test
            result = await orchestrator.execute_accessibility_test(url, test_options)
            
            if result.get('status') == 'completed':
                test_results = result['results']
                
                # Save results to file
                with open(output, 'w') as f:
                    json.dump(test_results, f, indent=2)
                
                # Display summary
                click.echo(f"\n✅ Test completed successfully!")
                click.echo(f"📊 Total issues found: {test_results.get('total_issues', 0)}")
                
                issues_by_severity = test_results.get('issues_by_severity', {})
                if issues_by_severity:
                    click.echo("📋 Issues by severity:")
                    for severity, count in issues_by_severity.items():
                        if count > 0:
                            click.echo(f"   {severity.upper()}: {count}")
                
                click.echo(f"📁 Full report saved to: {output}")
                
                # Show A2A usage
                remote_agents = test_results.get('remote_agents_used', 0)
                if remote_agents > 0:
                    click.echo(f"🌐 Remote agents used via A2A protocol: {remote_agents}")
                
            else:
                click.echo(f"❌ Test failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            click.echo(f"❌ Test execution failed: {e}")
            logger.error(f"Test execution error: {e}")
    
    # Execute the async test
    asyncio.run(run_test())

@cli.command()
@click.option('--url', type=str, help='Target URL for testing')
def chat(url: Optional[str]):
    """Interactive ADK agent chat for accessibility testing with A2A support"""
    click.echo("🤖 ADK Accessibility Testing Agent - Interactive Mode")
    click.echo("💬 Type your accessibility testing requests (or 'quit' to exit)")
    click.echo("🌐 A2A Protocol enabled for remote agent coordination")
    if url:
        click.echo(f"🎯 Default URL: {url}")
    click.echo("")
    
    async def chat_session():
        try:
            # Initialize ADK orchestrator
            orchestrator = ADKAccessibilityOrchestrator()
            
            # Start interactive session
            session_id = await orchestrator.start_interactive_session()
            click.echo(f"📝 Started session: {session_id}")
            click.echo("")
            
            while True:
                try:
                    # Get user input
                    prompt = click.prompt("👤", type=str, show_default=False)
                    
                    # Check for exit commands
                    if prompt.lower() in ['quit', 'exit', 'q']:
                        click.echo("👋 Goodbye!")
                        await orchestrator.cleanup_session(session_id)
                        break
                    
                    # Special commands
                    if prompt.lower() == 'list sessions':
                        sessions = await orchestrator.list_active_sessions()
                        click.echo(f"Active sessions: {len(sessions)}")
                        for session in sessions:
                            click.echo(f"  • {session['session_id']}: {session['state']}")
                        continue
                    
                    if prompt.lower() == 'discover agents':
                        remote_agents = await orchestrator.discover_remote_agents()
                        click.echo(f"🌐 Found {len(remote_agents)} remote agents via A2A:")
                        for agent in remote_agents:
                            click.echo(f"  • {agent['name']}: {agent['endpoint']}")
                        continue
                    
                    if prompt.lower() == 'agent capabilities':
                        caps = await orchestrator.get_agent_capabilities()
                        click.echo("🔧 Agent capabilities:")
                        click.echo(json.dumps(caps, indent=2))
                        continue
                    
                    # Process through ADK greeter agent
                    click.echo(f"🤖 Processing: {prompt}")
                    response = await orchestrator.process_user_input(session_id, prompt)
                    
                    click.echo(f"🤖 {response.get('greeting', 'Response received')}")
                    if response.get('next_steps'):
                        click.echo("📋 Next steps:")
                        for step in response['next_steps']:
                            click.echo(f"  • {step}")
                    
                    # If this looks like a URL, offer to test it
                    if 'http' in prompt.lower():
                        test_it = click.confirm("🧪 Would you like to run accessibility testing on this URL?")
                        if test_it:
                            test_result = await orchestrator.execute_accessibility_test(
                                prompt.strip(), 
                                session_id=session_id
                            )
                            if test_result.get('status') == 'completed':
                                results = test_result['results']
                                click.echo(f"✅ Test completed: {results.get('total_issues', 0)} issues found")
                            else:
                                click.echo(f"❌ Test failed: {test_result.get('error')}")
                    
                    click.echo("")
                    
                except (KeyboardInterrupt, EOFError):
                    click.echo("\n👋 Goodbye!")
                    await orchestrator.cleanup_session(session_id)
                    break
                except Exception as e:
                    click.echo(f"❌ Error: {e}")
                    click.echo("")
                    
        except Exception as e:
            click.echo(f"❌ Failed to start chat session: {e}")
    
    # Run the async chat session
    asyncio.run(chat_session())

@cli.command()
def list_agents():
    """List available ADK accessibility testing agents with A2A support"""
    async def show_agents():
        try:
            # Initialize ADK orchestrator
            orchestrator = ADKAccessibilityOrchestrator()
            capabilities = await orchestrator.get_agent_capabilities()
            
            click.echo("🤖 ADK Accessibility Testing Agents:")
            click.echo(f"📦 Framework: {capabilities.get('framework', 'Google ADK Python')}")
            click.echo(f"🌐 A2A Protocol: {'Enabled' if capabilities.get('a2a_protocol') else 'Disabled'}")
            click.echo("")
            
            for agent_type, agent_info in capabilities.get('agents', {}).items():
                click.echo(f"  • {agent_info.get('name', agent_type)}:")
                click.echo(f"    Type: {agent_info.get('type', 'unknown')}")
                click.echo(f"    Description: {agent_info.get('description', 'No description')}")
                if 'sub_agents' in agent_info:
                    click.echo(f"    Sub-agents: {agent_info['sub_agents']}")
                click.echo("")
              # Show remote agents if available
            remote_agents = await orchestrator.discover_remote_agents()
            if remote_agents:
                click.echo("🌐 Remote agents (via A2A protocol):")
                for agent in remote_agents:
                    click.echo(f"  • {agent['name']}: {agent['endpoint']}")
            else:
                click.echo("🌐 No remote agents discovered")
                
        except Exception as e:
            click.echo(f"❌ Failed to list agents: {e}")
    
    asyncio.run(show_agents())

@cli.command()
@click.argument('endpoint')
def test_a2a(endpoint: str):
    """Test A2A protocol communication with a remote agent"""
    async def test_communication():
        try:
            # Initialize ADK orchestrator
            orchestrator = ADKAccessibilityOrchestrator()
            
            click.echo(f"🌐 Testing A2A communication with: {endpoint}")
            result = await orchestrator.test_a2a_communication(endpoint)
            
            if result.get('status') == 'success':
                click.echo(f"✅ A2A communication successful!")
                click.echo(f"⏱️ Latency: {result.get('latency_ms')}ms")
                click.echo(f"📋 Protocol: {result.get('protocol_version')}")
            else:
                click.echo(f"❌ A2A communication failed: {result.get('error')}")
                
        except Exception as e:
            click.echo(f"❌ A2A test failed: {e}")
    
    asyncio.run(test_communication())

if __name__ == "__main__":
    cli()

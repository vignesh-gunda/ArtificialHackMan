# Main entry point - loads supervisor using DeepAgents
from deep_agent.supervisor import Supervisor
from deep_agent.config import DeepAgentConfig

def main():
    """Main application entry point"""
    # Initialize configuration
    config = DeepAgentConfig()
    app_config = config.load_config()
    
    # Initialize supervisor
    supervisor = Supervisor()
    supervisor.initialize_subagents()
    
    # Start the application
    print("Starting DeepAgent application...")
    
    # Example workflow coordination
    task = {
        "type": "document_processing",
        "input": "sample_document.pdf",
        "output_format": "video"
    }
    
    supervisor.coordinate_workflow(task)

if __name__ == "__main__":
    main()
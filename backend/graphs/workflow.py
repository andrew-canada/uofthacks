"""
LangGraph Workflow Definition.
Defines the complete product optimization workflow as a graph.
"""

from typing import Dict, Any
import sys
import os

# Note: This requires langgraph to be installed
# pip install langgraph langchain-core

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .state import GraphState, WorkflowConfig
from .nodes import (
    fetch_products_node,
    fetch_trends_node,
    analyze_products_node,
    generate_recommendations_node,
    apply_updates_node,
    should_continue_to_analysis,
    should_apply_updates
)

# Try to import langgraph
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ langgraph not installed. Workflow will use sequential execution.")


def create_optimization_workflow(config: WorkflowConfig = None):
    """
    Create the product optimization workflow graph.
    
    The workflow follows this pattern:
    1. Fetch products (parallel with trends)
    2. Fetch trends (parallel with products)
    3. Analyze products against trends (AI)
    4. Generate recommendations
    5. Optionally apply updates
    
    Args:
        config: Workflow configuration
        
    Returns:
        Compiled workflow graph or simple executor
    """
    if config is None:
        config = WorkflowConfig()
    
    if not LANGGRAPH_AVAILABLE:
        return SimpleWorkflowExecutor(config)
    
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("fetch_products", fetch_products_node)
    workflow.add_node("fetch_trends", fetch_trends_node)
    workflow.add_node("analyze", analyze_products_node)
    workflow.add_node("recommend", generate_recommendations_node)
    workflow.add_node("apply", apply_updates_node)
    
    # Define edges
    workflow.set_entry_point("fetch_products")
    
    # Parallel fetch: products and trends
    workflow.add_edge("fetch_products", "fetch_trends")
    
    # After trends, analyze
    workflow.add_conditional_edges(
        "fetch_trends",
        should_continue_to_analysis,
        {
            "analyze": "analyze",
            "error": END
        }
    )
    
    # After analysis, generate recommendations
    workflow.add_edge("analyze", "recommend")
    
    # Conditional: apply updates or finish
    if config.auto_apply and not config.dry_run:
        workflow.add_conditional_edges(
            "recommend",
            should_apply_updates,
            {
                "apply": "apply",
                "done": END,
                "error": END
            }
        )
        workflow.add_edge("apply", END)
    else:
        workflow.add_edge("recommend", END)
    
    return workflow.compile()


class SimpleWorkflowExecutor:
    """
    Fallback sequential executor when LangGraph is not available.
    Executes nodes in order without graph capabilities.
    """
    
    def __init__(self, config: WorkflowConfig):
        self.config = config
    
    def invoke(self, initial_state: Dict[str, Any] = None) -> GraphState:
        """
        Execute the workflow sequentially.
        
        Args:
            initial_state: Initial state values
            
        Returns:
            Final state after workflow completion
        """
        state: GraphState = initial_state or {}
        
        # Step 1: Fetch products
        print("📦 Fetching products...")
        state.update(fetch_products_node(state))
        
        if state.get('error'):
            return state
        
        # Step 2: Fetch trends
        print("📈 Fetching trends...")
        state.update(fetch_trends_node(state))
        
        if state.get('error'):
            return state
        
        # Step 3: Analyze
        print("🤖 Analyzing with AI...")
        state.update(analyze_products_node(state))
        
        if state.get('error'):
            return state
        
        # Step 4: Generate recommendations
        print("💡 Generating recommendations...")
        state.update(generate_recommendations_node(state))
        
        # Step 5: Apply updates (if configured)
        if self.config.auto_apply and not self.config.dry_run:
            print("✏️ Applying updates...")
            state.update(apply_updates_node(state))
        
        print("✅ Workflow complete!")
        return state


def run_optimization(
    product_ids: list = None,
    auto_apply: bool = False,
    dry_run: bool = True
) -> GraphState:
    """
    Convenience function to run the optimization workflow.
    
    Args:
        product_ids: Specific products to analyze (None for all)
        auto_apply: Whether to automatically apply recommendations
        dry_run: If True, don't actually update Shopify
        
    Returns:
        Final workflow state with all results
    """
    config = WorkflowConfig(
        auto_apply=auto_apply,
        dry_run=dry_run
    )
    
    workflow = create_optimization_workflow(config)
    
    initial_state = {}
    if product_ids:
        initial_state['product_ids'] = product_ids
    
    return workflow.invoke(initial_state)

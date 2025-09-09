# 🚀 Cursor Prompt: PostgreSQL SQL Analyzer Improvements

## 📋 Context
You are working on a PostgreSQL SQL Analyzer Streamlit application with the following current architecture:

- **Main App**: `app/streamlit_app.py` (600+ lines)
- **Plan Parser**: `app/plan_parser.py` (274 lines) 
- **Metrics**: `app/metrics.py` (362 lines)
- **Config**: `app/config.py` (127 lines)
- **UI Components**: `app/ui/` directory with 7 tabs
- **Styling**: `.streamlit/static/style.css` (376 lines)
- **Current Theme**: Dark theme with PostgreSQL colors

## 🎯 Mission
Transform this application into a professional enterprise-grade SQL analysis tool with AI capabilities, following the improvement plan below.

## 📊 Current State Analysis
- ✅ Basic EXPLAIN analysis with JSON parsing
- ✅ LLM integration (OpenAI, Anthropic, local models)
- ✅ Basic recommendation engine
- ✅ Dark theme with PostgreSQL branding
- ✅ SSH tunneling for security
- ✅ SQL validation for dangerous operations

## 🔴 HIGH PRIORITY TASKS (Implement First)

### 1. Deep EXPLAIN Analysis Enhancement
**File**: `app/plan_parser.py`
**Goal**: Transform basic JSON parsing into comprehensive plan analysis

```python
# ADD these classes to plan_parser.py
class AdvancedPlanAnalyzer:
    def analyze_parallel_execution(self, plan: Dict) -> ParallelExecutionMetrics
    def detect_n_plus_one_queries(self, plans: List[Dict]) -> List[NPlusOneIssue]
    def analyze_lock_contention(self, plan: Dict) -> LockContentionAnalysis
    def predict_resource_usage(self, plan: Dict, workload: WorkloadProfile) -> ResourcePrediction

class ParallelExecutionMetrics:
    max_workers: int
    parallel_scan_ratio: float
    parallel_join_ratio: float
    estimated_speedup: float

class NPlusOneIssue:
    pattern_type: str
    affected_queries: List[str]
    estimated_impact: float
    suggested_fix: str
```

**Implementation Steps**:
1. Extend existing `PlanParser` class with new analysis methods
2. Add detection algorithms for common performance anti-patterns
3. Integrate with existing `QueryMetrics` class
4. Update UI to display new metrics

### 2. Plan Comparison Engine
**File**: `app/ui/explain_analysis.py`
**Goal**: Add "before/after" comparison functionality

```python
# ADD to explain_analysis.py
class PlanComparisonEngine:
    def compare_plans(self, original: Dict, optimized: Dict) -> ComparisonResult
    def predict_performance_impact(self, changes: List[Optimization]) -> PerformanceImpact
    def generate_optimization_report(self, comparison: ComparisonResult) -> OptimizationReport

class ComparisonResult:
    cost_improvement: float
    time_improvement: float
    io_improvement: float
    memory_improvement: float
    recommendations: List[str]
```

**Implementation Steps**:
1. Add plan saving/loading functionality to session state
2. Create comparison UI components
3. Add side-by-side plan visualization
4. Integrate with AI for optimization suggestions

### 3. Intelligent Recommendation Engine
**File**: `app/recommendations.py`
**Goal**: Enhance basic rules with AI-contextual recommendations

```python
# EXTEND existing RecommendationEngine class
class IntelligentRecommendationEngine(RecommendationEngine):
    def analyze_index_candidates(self, plan: Dict, schema: Schema) -> List[IndexRecommendation]
    def suggest_sql_rewrites(self, sql: str, plan: Dict) -> List[SQLRewrite]
    def detect_n_plus_one_patterns(self, queries: List[str]) -> List[NPlusOneIssue]
    def generate_optimization_strategies(self, analysis: AnalysisResult) -> List[Strategy]

class IndexRecommendation:
    table_name: str
    columns: List[str]
    index_type: str
    estimated_benefit: float
    ddl_statement: str
    reasoning: str
```

**Implementation Steps**:
1. Extend existing `RecommendationEngine` class
2. Add schema analysis capabilities
3. Integrate with LLM for contextual recommendations
4. Add index candidate detection algorithms

## 🟡 MEDIUM PRIORITY TASKS

### 4. Interactive Plan Visualization
**File**: `app/ui/explain_analysis.py`
**Goal**: Replace simple tables with interactive Plotly visualizations

```python
# ADD to explain_analysis.py
class InteractivePlanVisualizer:
    def create_interactive_tree(self, plan: Dict) -> InteractiveTree
    def add_performance_heatmap(self, tree: InteractiveTree) -> HeatmapTree
    def enable_drill_down_analysis(self, node: PlanNode) -> DetailedAnalysis

def create_plan_tree_plotly(plan_data: List[Dict]) -> go.Figure:
    # Create interactive tree visualization with Plotly
    # Include hover information, click handlers, performance metrics
    pass
```

**Implementation Steps**:
1. Replace existing `_display_plan_tree_visualization` with Plotly
2. Add interactive features (hover, click, zoom)
3. Create performance heatmaps
4. Add drill-down capabilities

### 5. CI/CD Integration
**File**: Create new `app/cicd/` directory
**Goal**: Add CLI interface for CI/CD pipelines

```python
# NEW FILE: app/cicd/analyzer.py
class CICDAnalyzer:
    def analyze_pull_request(self, pr_data: PRData) -> CICDReport
    def check_query_performance(self, sql_files: List[str]) -> PerformanceReport
    def generate_ci_recommendations(self, analysis: AnalysisResult) -> List[CIRecommendation]

# NEW FILE: app/cli_cicd.py
@click.command()
@click.option('--sql-file', help='SQL file to analyze')
@click.option('--output-format', default='json', help='Output format')
def analyze_sql_file(sql_file, output_format):
    # CLI interface for CI/CD integration
    pass
```

**Implementation Steps**:
1. Create CLI interface using Click
2. Add GitHub Actions workflow file
3. Create CI/CD specific analysis functions
4. Add performance threshold checking

### 6. Workload Prediction
**File**: Create new `app/prediction/` directory
**Goal**: Add ML-based performance prediction

```python
# NEW FILE: app/prediction/workload_predictor.py
class WorkloadPredictor:
    def predict_query_performance(self, sql: str, workload: WorkloadProfile) -> PerformancePrediction
    def identify_bottlenecks(self, metrics: List[QueryMetrics]) -> List[Bottleneck]
    def suggest_scaling_strategies(self, predictions: List[PerformancePrediction]) -> List[ScalingStrategy]

# Add to requirements.txt:
# scikit-learn>=1.3.0
# numpy>=1.24.0
```

**Implementation Steps**:
1. Add ML dependencies to requirements.txt
2. Create prediction models
3. Add training data collection
4. Integrate with existing metrics system

## 🟢 LOW PRIORITY TASKS

### 7. Enhanced Streamlit Configuration
**File**: `.streamlit/config.toml`
**Goal**: Professional PostgreSQL-themed dark interface

```toml
[theme]
# PostgreSQL Professional Dark Theme
primaryColor = "#336791"      # PostgreSQL blue
backgroundColor = "#1a1a2e"   # Dark purple background
secondaryBackgroundColor = "#16213e"  # Secondary purple
textColor = "#ffffff"         # White text
font = "Inter"               # Modern font
base = "dark"

[ui]
hideTopBar = true
hideSidebarNav = true
```

**File**: `.streamlit/static/style.css`
**Goal**: Enhanced CSS with PostgreSQL branding

```css
:root {
    --postgres-blue: #336791;
    --postgres-dark: #1a1a2e;
    --postgres-purple: #7b68ee;
    --postgres-accent: #4a90a4;
    --gradient-primary: linear-gradient(135deg, #336791 0%, #7b68ee 100%);
    --gradient-secondary: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

/* Add PostgreSQL-themed components */
.postgres-card {
    background: var(--gradient-primary);
    border-radius: 12px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(51, 103, 145, 0.3);
}
```

### 8. Role-Based UI Tabs
**File**: `app/streamlit_app.py`
**Goal**: Specialized tabs for different user roles

```python
# MODIFY main() function in streamlit_app.py
def main():
    # Add role selection
    user_role = st.sidebar.selectbox(
        "Select Role",
        ["Performance Analyst", "DBA", "Developer", "Manager"],
        help="Choose your role for customized interface"
    )
    
    # Show different tabs based on role
    if user_role == "Performance Analyst":
        show_performance_analyst_tabs()
    elif user_role == "DBA":
        show_dba_tabs()
    # ... etc
```

## 🛠️ Implementation Guidelines

### Code Quality Standards
- Follow existing code patterns in the project
- Add type hints for all new functions
- Include docstrings with examples
- Write unit tests for new functionality
- Update existing tests when modifying code

### File Organization
- Keep new classes in appropriate existing files when possible
- Create new directories only when adding major new functionality
- Maintain the existing modular architecture
- Update imports in `__init__.py` files

### UI/UX Consistency
- Follow existing Streamlit patterns
- Use consistent color scheme from CSS variables
- Maintain responsive design
- Add loading states for long operations
- Include helpful tooltips and help text

### Testing Strategy
- Test new analysis algorithms with sample data
- Verify UI components work across different screen sizes
- Test CI/CD integration with sample SQL files
- Validate ML predictions with known datasets

## 🎯 Success Metrics
- **Analysis Quality**: 400% improvement in recommendation accuracy
- **User Experience**: 300% improvement in interface usability
- **Performance**: 200% faster analysis processing
- **Integration**: Seamless CI/CD pipeline integration
- **Visual Appeal**: Professional PostgreSQL-themed interface

## 🚀 Getting Started
1. Start with HIGH PRIORITY tasks
2. Implement one feature at a time
3. Test thoroughly before moving to next feature
4. Update documentation as you go
5. Maintain backward compatibility

## 📝 Notes
- The existing codebase is well-structured and modular
- LLM integration is already working - build upon it
- The dark theme is already implemented - enhance it
- Focus on adding value, not rewriting existing functionality
- Keep the existing 7-tab structure but enhance each tab

Remember: This is an enhancement project, not a rewrite. Build upon the solid foundation that already exists!

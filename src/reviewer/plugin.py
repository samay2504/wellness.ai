"""
Code Review Plugin for Wellness at Work
Automated code analysis and quality assurance
"""

import ast
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Issue severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueType(Enum):
    """Types of code issues"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"


@dataclass
class CodeIssue:
    """Represents a code quality issue"""
    file_path: str
    line_number: int
    column: int
    severity: IssueSeverity
    issue_type: IssueType
    message: str
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None


class CodeReviewer:
    """Main code review class"""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
        self.security_patterns = self._load_security_patterns()
        self.performance_patterns = self._load_performance_patterns()
    
    def _load_security_patterns(self) -> Dict[str, re.Pattern]:
        """Load security-related regex patterns"""
        return {
            "sql_injection": re.compile(r"execute\(.*\+.*\)", re.IGNORECASE),
            "hardcoded_password": re.compile(r"password\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
            "weak_crypto": re.compile(r"md5|sha1", re.IGNORECASE),
            "eval_usage": re.compile(r"\beval\s*\(", re.IGNORECASE),
            "exec_usage": re.compile(r"\bexec\s*\(", re.IGNORECASE),
            "pickle_unsafe": re.compile(r"pickle\.loads\s*\(", re.IGNORECASE),
            "shell_injection": re.compile(r"os\.system|subprocess\.call.*\+", re.IGNORECASE),
        }
    
    def _load_performance_patterns(self) -> Dict[str, re.Pattern]:
        """Load performance-related regex patterns"""
        return {
            "n_plus_one": re.compile(r"for.*in.*:\s*\n.*\.query\(", re.IGNORECASE),
            "inefficient_loop": re.compile(r"for.*in.*range\(len\(", re.IGNORECASE),
            "memory_leak": re.compile(r"global\s+\w+", re.IGNORECASE),
            "unused_import": re.compile(r"import\s+\w+", re.IGNORECASE),
        }
    
    def review_file(self, file_path: str) -> List[CodeIssue]:
        """Review a single file for issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.issues = []
            
            # Parse AST for structural analysis
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, file_path)
            except SyntaxError as e:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    column=e.offset or 1,
                    severity=IssueSeverity.CRITICAL,
                    issue_type=IssueType.STYLE,
                    message=f"Syntax error: {e.msg}",
                    rule_id="SYNTAX_ERROR"
                ))
            
            # Pattern-based analysis
            self._analyze_patterns(content, file_path)
            
            # Style analysis
            self._analyze_style(content, file_path)
            
            return self.issues
            
        except Exception as e:
            logger.error(f"Error reviewing file {file_path}: {e}")
            return []
    
    def _analyze_ast(self, tree: ast.AST, file_path: str):
        """Analyze AST for code quality issues"""
        for node in ast.walk(tree):
            # Check for security issues
            if isinstance(node, ast.Call):
                self._check_function_calls(node, file_path)
            
            # Check for performance issues
            if isinstance(node, ast.For):
                self._check_loop_efficiency(node, file_path)
            
            # Check for maintainability issues
            if isinstance(node, ast.FunctionDef):
                self._check_function_complexity(node, file_path)
    
    def _check_function_calls(self, node: ast.Call, file_path: str):
        """Check function calls for security issues"""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            
            # Check for dangerous functions
            dangerous_funcs = ['eval', 'exec', 'os.system', 'subprocess.call']
            if func_name in dangerous_funcs:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=getattr(node, 'lineno', 0),
                    column=getattr(node, 'col_offset', 0),
                    severity=IssueSeverity.HIGH,
                    issue_type=IssueType.SECURITY,
                    message=f"Dangerous function call: {func_name}",
                    suggestion=f"Consider using safer alternatives to {func_name}",
                    rule_id="DANGEROUS_FUNCTION"
                ))
    
    def _check_loop_efficiency(self, node: ast.For, file_path: str):
        """Check loops for performance issues"""
        # Check for range(len()) pattern
        if (isinstance(node.iter, ast.Call) and 
            isinstance(node.iter.func, ast.Name) and 
            node.iter.func.id == 'range'):
            
            if (node.iter.args and 
                isinstance(node.iter.args[0], ast.Call) and
                isinstance(node.iter.args[0].func, ast.Name) and
                node.iter.args[0].func.id == 'len'):
                
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=getattr(node, 'lineno', 0),
                    column=getattr(node, 'col_offset', 0),
                    severity=IssueSeverity.MEDIUM,
                    issue_type=IssueType.PERFORMANCE,
                    message="Inefficient loop using range(len())",
                    suggestion="Use enumerate() or direct iteration instead",
                    rule_id="INEFFICIENT_LOOP"
                ))
    
    def _check_function_complexity(self, node: ast.FunctionDef, file_path: str):
        """Check function complexity"""
        complexity = self._calculate_complexity(node)
        
        if complexity > 10:
            self.issues.append(CodeIssue(
                file_path=file_path,
                line_number=getattr(node, 'lineno', 0),
                column=getattr(node, 'col_offset', 0),
                severity=IssueSeverity.MEDIUM,
                issue_type=IssueType.MAINTAINABILITY,
                message=f"Function '{node.name}' has high complexity ({complexity})",
                suggestion="Consider breaking down the function into smaller functions",
                rule_id="HIGH_COMPLEXITY"
            ))
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _analyze_patterns(self, content: str, file_path: str):
        """Analyze content using regex patterns"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check security patterns
            for pattern_name, pattern in self.security_patterns.items():
                if pattern.search(line):
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=line_num,
                        column=1,
                        severity=IssueSeverity.HIGH,
                        issue_type=IssueType.SECURITY,
                        message=f"Potential security issue: {pattern_name}",
                        suggestion="Review this line for security implications",
                        rule_id=f"SECURITY_{pattern_name.upper()}"
                    ))
            
            # Check performance patterns
            for pattern_name, pattern in self.performance_patterns.items():
                if pattern.search(line):
                    self.issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=line_num,
                        column=1,
                        severity=IssueSeverity.MEDIUM,
                        issue_type=IssueType.PERFORMANCE,
                        message=f"Potential performance issue: {pattern_name}",
                        suggestion="Consider optimizing this code",
                        rule_id=f"PERFORMANCE_{pattern_name.upper()}"
                    ))
    
    def _analyze_style(self, content: str, file_path: str):
        """Analyze code style"""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # Check line length
            if len(line) > 120:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=line_num,
                    column=1,
                    severity=IssueSeverity.LOW,
                    issue_type=IssueType.STYLE,
                    message="Line too long",
                    suggestion="Break long lines to improve readability",
                    rule_id="LINE_TOO_LONG"
                ))
            
            # Check for trailing whitespace
            if line.rstrip() != line:
                self.issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=line_num,
                    column=len(line.rstrip()) + 1,
                    severity=IssueSeverity.LOW,
                    issue_type=IssueType.STYLE,
                    message="Trailing whitespace",
                    suggestion="Remove trailing whitespace",
                    rule_id="TRAILING_WHITESPACE"
                ))
    
    def review_directory(self, directory_path: str, extensions: List[str] = None) -> List[CodeIssue]:
        """Review all files in a directory"""
        if extensions is None:
            extensions = ['.py', '.js', '.jsx', '.ts', '.tsx']
        
        all_issues = []
        directory = Path(directory_path)
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                issues = self.review_file(str(file_path))
                all_issues.extend(issues)
        
        return all_issues
    
    def generate_report(self, issues: List[CodeIssue]) -> Dict[str, Any]:
        """Generate a summary report of issues"""
        if not issues:
            return {
                "summary": "No issues found",
                "total_issues": 0,
                "by_severity": {},
                "by_type": {},
                "files_affected": 0
            }
        
        # Group by severity
        by_severity = {}
        for severity in IssueSeverity:
            by_severity[severity.value] = len([i for i in issues if i.severity == severity])
        
        # Group by type
        by_type = {}
        for issue_type in IssueType:
            by_type[issue_type.value] = len([i for i in issues if i.issue_type == issue_type])
        
        # Count unique files
        files_affected = len(set(i.file_path for i in issues))
        
        return {
            "summary": f"Found {len(issues)} issues across {files_affected} files",
            "total_issues": len(issues),
            "by_severity": by_severity,
            "by_type": by_type,
            "files_affected": files_affected,
            "issues": [
                {
                    "file": i.file_path,
                    "line": i.line_number,
                    "column": i.column,
                    "severity": i.severity.value,
                    "type": i.issue_type.value,
                    "message": i.message,
                    "suggestion": i.suggestion,
                    "rule_id": i.rule_id
                }
                for i in issues
            ]
        }


class SecurityReviewer(CodeReviewer):
    """Specialized reviewer for security issues"""
    
    def __init__(self):
        super().__init__()
        self.security_patterns.update({
            "jwt_secret": re.compile(r"JWT_SECRET\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
            "api_key": re.compile(r"API_KEY\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
            "database_url": re.compile(r"DATABASE_URL\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE),
            "cors_wildcard": re.compile(r"CORS\(.*\*.*\)", re.IGNORECASE),
            "debug_mode": re.compile(r"DEBUG\s*=\s*True", re.IGNORECASE),
        })
    
    def review_security(self, file_path: str) -> List[CodeIssue]:
        """Focus on security-specific issues"""
        issues = self.review_file(file_path)
        return [i for i in issues if i.issue_type == IssueType.SECURITY]


class PerformanceReviewer(CodeReviewer):
    """Specialized reviewer for performance issues"""
    
    def __init__(self):
        super().__init__()
        self.performance_patterns.update({
            "nested_loop": re.compile(r"for.*:\s*\n.*for.*:", re.IGNORECASE),
            "inefficient_query": re.compile(r"\.all\(\)\.filter\(", re.IGNORECASE),
            "memory_intensive": re.compile(r"list\(.*\)\.append", re.IGNORECASE),
        })
    
    def review_performance(self, file_path: str) -> List[CodeIssue]:
        """Focus on performance-specific issues"""
        issues = self.review_file(file_path)
        return [i for i in issues if i.issue_type == IssueType.PERFORMANCE]


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Review Tool")
    parser.add_argument("path", help="File or directory to review")
    parser.add_argument("--type", choices=["all", "security", "performance"], 
                       default="all", help="Type of review to perform")
    parser.add_argument("--output", help="Output file for report")
    parser.add_argument("--format", choices=["json", "text"], default="text",
                       help="Output format")
    
    args = parser.parse_args()
    
    # Initialize appropriate reviewer
    if args.type == "security":
        reviewer = SecurityReviewer()
    elif args.type == "performance":
        reviewer = PerformanceReviewer()
    else:
        reviewer = CodeReviewer()
    
    # Perform review
    path = Path(args.path)
    if path.is_file():
        issues = reviewer.review_file(str(path))
    else:
        issues = reviewer.review_directory(str(path))
    
    # Generate report
    report = reviewer.generate_report(issues)
    
    # Output results
    if args.output:
        import json
        with open(args.output, 'w') as f:
            if args.format == "json":
                json.dump(report, f, indent=2)
            else:
                f.write(f"Code Review Report\n")
                f.write(f"=================\n\n")
                f.write(f"{report['summary']}\n\n")
                f.write(f"Total Issues: {report['total_issues']}\n")
                f.write(f"Files Affected: {report['files_affected']}\n\n")
                
                for issue in report['issues']:
                    f.write(f"{issue['file']}:{issue['line']}:{issue['column']} - ")
                    f.write(f"{issue['severity'].upper()} - {issue['message']}\n")
                    if issue['suggestion']:
                        f.write(f"  Suggestion: {issue['suggestion']}\n")
                    f.write("\n")
    else:
        print(f"Code Review Report")
        print(f"=================")
        print(f"{report['summary']}")
        print(f"Total Issues: {report['total_issues']}")
        print(f"Files Affected: {report['files_affected']}")
        
        for issue in report['issues']:
            print(f"{issue['file']}:{issue['line']}:{issue['column']} - "
                  f"{issue['severity'].upper()} - {issue['message']}")
            if issue['suggestion']:
                print(f"  Suggestion: {issue['suggestion']}")


if __name__ == "__main__":
    main() 
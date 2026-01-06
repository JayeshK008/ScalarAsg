"""
Sanity check for all model classes.
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import (
    Organization, Team, User, TeamMembership,
    Project, Section, Task, Comment,
    CustomFieldDefinition, CustomFieldEnumOption, CustomFieldValue,
    Tag, TaskTag, Attachment
)


class ModelTester:
    """Test harness for model validation."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test_model(self, model_name, model_instance, expected_keys):
        """
        Test a model instance:
        1. Can instantiate
        2. Has to_dict() method
        3. to_dict() returns expected keys
        4. No None values where not allowed
        """
        try:
            # Test 1: Instance created
            assert model_instance is not None, f"{model_name} instance is None"
            
            # Test 2: Has to_dict method
            assert hasattr(model_instance, 'to_dict'), f"{model_name} missing to_dict()"
            
            # Test 3: to_dict() returns dict
            result = model_instance.to_dict()
            assert isinstance(result, dict), f"{model_name}.to_dict() didn't return dict"
            
            # Test 4: Check expected keys
            missing_keys = set(expected_keys) - set(result.keys())
            assert not missing_keys, f"{model_name} missing keys: {missing_keys}"
            
            # Test 5: No invalid types (all should be JSON-serializable)
            for key, value in result.items():
                if value is not None:
                    assert isinstance(value, (str, int, float, bool, type(None))), \
                        f"{model_name}.{key} has invalid type: {type(value)}"
            
            print(f" {model_name:30} PASSED")
            self.passed += 1
            return True
            
        except AssertionError as e:
            print(f" {model_name:30} FAILED: {str(e)}")
            self.failed += 1
            self.errors.append(f"{model_name}: {str(e)}")
            return False
        except Exception as e:
            print(f" {model_name:30} ERROR: {str(e)}")
            self.failed += 1
            self.errors.append(f"{model_name}: {str(e)}")
            return False
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*70)
        print("MODEL VALIDATION SUMMARY")
        print("="*70)
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Total:  {self.passed + self.failed}")
        
        if self.errors:
            print("\n" + "="*70)
            print("ERRORS:")
            print("="*70)
            for error in self.errors:
                print(f"  • {error}")
        
        print("\n" + "="*70)
        if self.failed == 0:
            print(" ALL MODELS PASSED - READY FOR GENERATORS")
        else:
            print(" FIX ERRORS BEFORE USING MODELS")
        print("="*70 + "\n")


def run_tests():
    """Run all model tests."""
    tester = ModelTester()
    
    print("\n" + "="*70)
    print("TESTING MODEL CLASSES")
    print("="*70 + "\n")
    
    # Test Organization
    org = Organization(
        organization_id="org_123",
        name="Test Corp",
        domain="testcorp.com",
        is_organization=True,
        created_at=datetime.now()
    )
    tester.test_model("Organization", org, 
                     ['organization_id', 'name', 'domain', 'is_organization', 'created_at'])
    
    # Test Team
    team = Team(
        team_id="team_123",
        organization_id="org_123",
        name="Engineering",
        team_type="Engineering",
        description="Core engineering team",
        privacy="public",
        created_at=datetime.now()
    )
    tester.test_model("Team", team,
                     ['team_id', 'organization_id', 'name', 'description', 
                      'team_type', 'privacy', 'created_at'])
    
    # Test User
    user = User(
        user_id="user_123",
        organization_id="org_123",
        email="john@testcorp.com",
        name="John Smith",
        role="member",
        department="Engineering",
        job_title="Software Engineer",
        is_active=True,
        workload_capacity=1.0,
        created_at=datetime.now(),
        last_active_at=datetime.now()
    )
    tester.test_model("User", user,
                     ['user_id', 'organization_id', 'email', 'name', 'role',
                      'department', 'job_title', 'photo_url', 'is_active',
                      'workload_capacity', 'created_at', 'last_active_at'])
    
    # Test TeamMembership
    membership = TeamMembership(
        membership_id="mem_123",
        team_id="team_123",
        user_id="user_123",
        role="member",
        joined_at=datetime.now()
    )
    tester.test_model("TeamMembership", membership,
                     ['membership_id', 'team_id', 'user_id', 'role', 'joined_at'])
    
    # Test Project
    project = Project(
        project_id="proj_123",
        organization_id="org_123",
        team_id="team_123",
        name="Q1 Sprint",
        description="Q1 engineering sprint",
        owner_id="user_123",
        project_type="sprint",
        privacy="team",
        status="active",
        color="blue",
        start_date=date.today(),
        due_date=date.today(),
        created_at=datetime.now()
    )
    tester.test_model("Project", project,
                     ['project_id', 'organization_id', 'team_id', 'name',
                      'description', 'owner_id', 'project_type', 'privacy',
                      'status', 'color', 'start_date', 'due_date', 
                      'completed_at', 'created_at'])
    
    # Test Section
    section = Section(
        section_id="sec_123",
        project_id="proj_123",
        name="To Do",
        position=1,
        created_at=datetime.now()
    )
    tester.test_model("Section", section,
                     ['section_id', 'project_id', 'name', 'position', 'created_at'])
    
    # Test Task
    task = Task(
        task_id="task_123",
        project_id="proj_123",
        section_id="sec_123",
        name="Implement feature X",
        description="Build the new feature",
        assignee_id="user_123",
        created_by="user_123",
        priority="high",
        due_date=date.today(),
        start_date=date.today(),
        completed=False,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    tester.test_model("Task", task,
                     ['task_id', 'project_id', 'section_id', 'parent_task_id',
                      'name', 'description', 'assignee_id', 'created_by',
                      'priority', 'due_date', 'start_date', 'completed',
                      'completed_at', 'created_at', 'modified_at'])
    
    # Test Subtask
    subtask = Task(
        task_id="task_124",
        project_id="proj_123",
        section_id="sec_123",
        parent_task_id="task_123",  # This makes it a subtask
        name="Subtask of feature X",
        created_by="user_123",
        created_at=datetime.now()
    )
    tester.test_model("Task (Subtask)", subtask,
                     ['task_id', 'project_id', 'section_id', 'parent_task_id',
                      'name', 'description', 'assignee_id', 'created_by',
                      'priority', 'due_date', 'start_date', 'completed',
                      'completed_at', 'created_at', 'modified_at'])
    
    # Test Comment
    comment = Comment(
        comment_id="comment_123",
        task_id="task_123",
        user_id="user_123",
        text="Great progress on this!",
        is_pinned=False,
        created_at=datetime.now()
    )
    tester.test_model("Comment", comment,
                     ['comment_id', 'task_id', 'user_id', 'text', 
                      'is_pinned', 'created_at'])
    
    # Test CustomFieldDefinition
    field_def = CustomFieldDefinition(
        field_id="field_123",
        project_id="proj_123",
        name="Story Points",
        field_type="number",
        description="Effort estimate",
        is_required=False,
        position=1,
        created_at=datetime.now()
    )
    tester.test_model("CustomFieldDefinition", field_def,
                     ['field_id', 'project_id', 'name', 'field_type',
                      'description', 'is_required', 'position', 'created_at'])
    
    # Test CustomFieldEnumOption
    enum_option = CustomFieldEnumOption(
        option_id="opt_123",
        field_id="field_123",
        value="High",
        color="red",
        position=1
    )
    tester.test_model("CustomFieldEnumOption", enum_option,
                     ['option_id', 'field_id', 'value', 'color', 'position'])
    
    # Test CustomFieldValue (number type)
    field_value_num = CustomFieldValue(
        value_id="val_123",
        task_id="task_123",
        field_id="field_123",
        value_number=5.0,
        created_at=datetime.now()
    )
    tester.test_model("CustomFieldValue (number)", field_value_num,
                     ['value_id', 'task_id', 'field_id', 'value_text',
                      'value_number', 'value_date', 'value_checkbox',
                      'value_enum_option_id', 'value_user_id', 'created_at'])
    
    # Test CustomFieldValue (text type)
    field_value_text = CustomFieldValue(
        value_id="val_124",
        task_id="task_123",
        field_id="field_124",
        value_text="Some description",
        created_at=datetime.now()
    )
    tester.test_model("CustomFieldValue (text)", field_value_text,
                     ['value_id', 'task_id', 'field_id', 'value_text',
                      'value_number', 'value_date', 'value_checkbox',
                      'value_enum_option_id', 'value_user_id', 'created_at'])
    
    # Test CustomFieldValue (date type)
    field_value_date = CustomFieldValue(
        value_id="val_125",
        task_id="task_123",
        field_id="field_125",
        value_date=date.today(),
        created_at=datetime.now()
    )
    tester.test_model("CustomFieldValue (date)", field_value_date,
                     ['value_id', 'task_id', 'field_id', 'value_text',
                      'value_number', 'value_date', 'value_checkbox',
                      'value_enum_option_id', 'value_user_id', 'created_at'])
    
    # Test CustomFieldValue (checkbox type)
    field_value_checkbox = CustomFieldValue(
        value_id="val_126",
        task_id="task_123",
        field_id="field_126",
        value_checkbox=True,
        created_at=datetime.now()
    )
    tester.test_model("CustomFieldValue (checkbox)", field_value_checkbox,
                     ['value_id', 'task_id', 'field_id', 'value_text',
                      'value_number', 'value_date', 'value_checkbox',
                      'value_enum_option_id', 'value_user_id', 'created_at'])
    
    # Test Tag
    tag = Tag(
        tag_id="tag_123",
        organization_id="org_123",
        name="urgent",
        color="red",
        created_at=datetime.now()
    )
    tester.test_model("Tag", tag,
                     ['tag_id', 'organization_id', 'name', 'color', 'created_at'])
    
    # Test TaskTag
    task_tag = TaskTag(
        task_tag_id="tt_123",
        task_id="task_123",
        tag_id="tag_123",
        created_at=datetime.now()
    )
    tester.test_model("TaskTag", task_tag,
                     ['task_tag_id', 'task_id', 'tag_id', 'created_at'])
    
    # Test Attachment
    attachment = Attachment(
        attachment_id="att_123",
        task_id="task_123",
        uploaded_by="user_123",
        filename="design.pdf",
        file_type="application/pdf",
        file_size_bytes=1024000,
        storage_url="s3://bucket/file.pdf",
        created_at=datetime.now()
    )
    tester.test_model("Attachment", attachment,
                     ['attachment_id', 'task_id', 'uploaded_by', 'filename',
                      'file_type', 'file_size_bytes', 'storage_url', 'created_at'])
    
    # Print summary
    tester.print_summary()
    
    # Return exit code
    return 0 if tester.failed == 0 else 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)

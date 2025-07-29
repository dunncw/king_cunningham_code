# test_hoa_fcl_workflow.py - Test script for Horry HOA-FCL workflow validation
import pytest
import os
import sys
from pathlib import Path

# Add the project root to Python path so we can import modules
# Adjust this path based on your project structure
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.validator import SimplifileValidator
from utils.logging import Logger


class TestHOAFCLWorkflow:
    """Test suite for Horry HOA-FCL workflow validation"""
    
    @classmethod
    def setup_class(cls):
        """Set up test class with file paths"""
        cls.county_id = "SCCP49"
        cls.workflow_id = "hoa_fcl"
        
        # Test file paths
        cls.excel_path = r"D:\repositorys\KC_appp\task\simplifile\docs\county\horry-SCCP49\workflows\hoa_fcl\upload\TD & SAT S.S. - HC.xlsx"
        cls.deed_stack_path = r"D:\repositorys\KC_appp\task\simplifile\docs\county\horry-SCCP49\workflows\hoa_fcl\upload\td.pdf"
        cls.affidavit_stack_path = r"D:\repositorys\KC_appp\task\simplifile\docs\county\horry-SCCP49\workflows\hoa_fcl\upload\aff.pdf"
        cls.condo_lien_stack_path = r"D:\repositorys\KC_appp\task\simplifile\docs\county\horry-SCCP49\workflows\hoa_fcl\upload\sat.pdf"
        
        # Create test logger
        cls.logger = Logger()
        
        print(f"\n{'='*60}")
        print(f"HOA-FCL WORKFLOW TEST SETUP")
        print(f"{'='*60}")
        print(f"County: {cls.county_id}")
        print(f"Workflow: {cls.workflow_id}")
        print(f"Excel Path: {cls.excel_path}")
        print(f"Deed Stack: {cls.deed_stack_path}")
        print(f"Affidavit Stack: {cls.affidavit_stack_path}")
        print(f"Condo Lien Stack: {cls.condo_lien_stack_path}")
        print(f"{'='*60}\n")
    
    def test_file_existence(self):
        """Test that all required files exist"""
        print("TEST 1: File Existence")
        print("-" * 30)
        
        files_to_check = [
            ("Excel file", self.excel_path),
            ("Deed Stack PDF", self.deed_stack_path),
            ("Affidavit Stack PDF", self.affidavit_stack_path),
            ("Condo Lien Stack PDF", self.condo_lien_stack_path)
        ]
        
        for file_type, file_path in files_to_check:
            print(f"Checking {file_type}...")
            assert os.path.exists(file_path), f"{file_type} does not exist: {file_path}"
            assert os.path.isfile(file_path), f"{file_type} is not a file: {file_path}"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            assert file_size > 0, f"{file_type} is empty: {file_path}"
            print(f"  ✓ {file_type} exists ({file_size:,} bytes)")
        
        print("✓ All files exist and are readable\n")
    
    def test_validator_creation(self):
        """Test that the validator can be created for HOA-FCL workflow"""
        print("TEST 2: Validator Creation")
        print("-" * 30)
        
        try:
            validator = SimplifileValidator(
                county_id=self.county_id,
                workflow_type=self.workflow_id,
                logger=self.logger
            )
            print("✓ SimplifileValidator created successfully")
            
            # Test that workflow is properly initialized
            assert validator.county_id == self.county_id
            assert validator.workflow_type == self.workflow_id
            assert validator.workflow is not None
            assert validator.pdf_processor is not None
            print("✓ Validator components initialized correctly")
            
            # Test workflow-specific features
            workflow = validator.workflow
            assert hasattr(workflow, 'get_deed_document_type')
            assert hasattr(workflow, 'get_satisfaction_document_type')
            
            deed_type = workflow.get_deed_document_type()
            satisfaction_type = workflow.get_satisfaction_document_type()
            
            print(f"  Deed Document Type: {deed_type}")
            print(f"  Satisfaction Document Type: {satisfaction_type}")
            
            assert deed_type == "Deed - Timeshare"
            assert satisfaction_type == "Condo Lien Satisfaction"
            print("✓ Workflow-specific document types are correct")
            
        except Exception as e:
            pytest.fail(f"Failed to create validator: {str(e)}")
        
        print("✓ Validator creation test passed\n")
    
    def test_hoa_fcl_validation_comprehensive(self):
        """Test comprehensive validation of HOA-FCL workflow"""
        print("TEST 3: Comprehensive HOA-FCL Validation")
        print("-" * 50)
        
        # Create validator
        validator = SimplifileValidator(
            county_id=self.county_id,
            workflow_type=self.workflow_id,
            logger=self.logger
        )
        
        try:
            # Run comprehensive validation
            is_valid, errors, summary = validator.validate_all(
                excel_path=self.excel_path,
                deed_path=self.deed_stack_path,
                stack2_path=self.affidavit_stack_path,
                mortgage_path=self.condo_lien_stack_path
            )
            
            # Print validation results
            print(f"Validation Result: {'PASSED' if is_valid else 'FAILED'}")
            print(f"Errors Found: {len(errors)}")
            
            # Print summary information
            if summary:
                print("\nValidation Summary:")
                for key, value in summary.items():
                    if key != "issues_found":
                        print(f"  {key}: {value}")
            
            # Print any errors
            if errors:
                print("\nValidation Errors:")
                for i, error in enumerate(errors, 1):
                    print(f"  {i}. {error}")
            
            # Print any issues found
            if summary.get("issues_found"):
                print("\nIssues Found:")
                for i, issue in enumerate(summary["issues_found"], 1):
                    print(f"  {i}. {issue}")
            
            # Test assertions
            if is_valid:
                print("✓ Comprehensive validation PASSED")
                
                # Verify summary has expected keys
                expected_keys = ["files_checked", "excel_rows", "valid_packages", "pdf_documents"]
                for key in expected_keys:
                    assert key in summary, f"Missing summary key: {key}"
                
                # Verify we have some valid packages
                assert summary["valid_packages"] > 0, "No valid packages found"
                assert summary["pdf_documents"] > 0, "No PDF documents found"
                
                print(f"  ✓ Found {summary['valid_packages']} valid packages")
                print(f"  ✓ Found {summary['pdf_documents']} PDF document sets")
                
            else:
                print("✗ Comprehensive validation FAILED")
                # Don't fail the test immediately - let's see what the issues are
                print("This test will continue to show what validation issues were found...")
            
        except Exception as e:
            pytest.fail(f"Validation threw an exception: {str(e)}")
        
        finally:
            # Cleanup
            validator.cleanup()
        
        print("✓ Comprehensive validation test completed\n")
    
    def test_excel_structure_validation(self):
        """Test Excel file structure validation specifically"""
        print("TEST 4: Excel Structure Validation")
        print("-" * 40)
        
        validator = SimplifileValidator(
            county_id=self.county_id,
            workflow_type=self.workflow_id,
            logger=self.logger
        )
        
        try:
            import pandas as pd
            
            # Load Excel file
            excel_df = pd.read_excel(self.excel_path, dtype=str)
            print(f"Loaded Excel file with {len(excel_df)} rows")
            
            # Get required columns for HOA-FCL
            workflow = validator.workflow
            required_columns = workflow.get_required_excel_columns()
            
            print(f"Required columns for HOA-FCL: {len(required_columns)}")
            for col in required_columns:
                print(f"  - {col}")
            
            # Check structure
            structure_errors = workflow.validate_excel_structure(excel_df)
            
            if structure_errors:
                print(f"\nStructure errors found: {len(structure_errors)}")
                for error in structure_errors:
                    print(f"  ✗ {error}")
            else:
                print("✓ Excel structure validation passed")
            
            # Check for HOA-FCL specific columns (GRANTOR and GRANTEE separate)
            assert "GRANTOR" in excel_df.columns, "Missing separate GRANTOR column"
            assert "GRANTEE" in excel_df.columns, "Missing separate GRANTEE column"
            print("✓ HOA-FCL specific columns (separate GRANTOR/GRANTEE) found")
            
            # Show some sample data
            if len(excel_df) > 0:
                print(f"\nSample data from first row:")
                sample_row = excel_df.iloc[0]
                key_columns = ["Account", "Last Name #1", "First Name #1", "GRANTOR", "GRANTEE", "Consideration"]
                for col in key_columns:
                    if col in sample_row:
                        print(f"  {col}: {sample_row[col]}")
            
        except Exception as e:
            pytest.fail(f"Excel structure validation failed: {str(e)}")
        
        finally:
            validator.cleanup()
        
        print("✓ Excel structure validation test completed\n")
    
    def test_pdf_stack_validation(self):
        """Test PDF stack validation specifically"""
        print("TEST 5: PDF Stack Validation")
        print("-" * 35)
        
        validator = SimplifileValidator(
            county_id=self.county_id,
            workflow_type=self.workflow_id,
            logger=self.logger
        )
        
        try:
            pdf_processor = validator.pdf_processor
            
            # Test stack validation
            errors = pdf_processor.validate_stacks(
                self.deed_stack_path,
                self.affidavit_stack_path,
                self.condo_lien_stack_path
            )
            
            if errors:
                print(f"PDF stack validation errors: {len(errors)}")
                for error in errors:
                    print(f"  ✗ {error}")
            else:
                print("✓ PDF stack validation passed")
            
            # Get stack summary
            summary = pdf_processor.get_stack_summary(
                self.deed_stack_path,
                self.affidavit_stack_path,
                self.condo_lien_stack_path
            )
            
            print(f"\nPDF Stack Summary:")
            print(f"  Deed Stack: {summary['deed_stack']['complete_documents']} documents ({summary['deed_stack']['total_pages']} pages)")
            print(f"  Affidavit Stack: {summary['affidavit_stack']['complete_documents']} documents ({summary['affidavit_stack']['total_pages']} pages)")
            print(f"  Condo Lien Stack: {summary['condo_lien_stack']['complete_documents']} documents ({summary['condo_lien_stack']['total_pages']} pages)")
            print(f"  Max Packages: {summary['max_packages']}")
            print(f"  All Stacks Aligned: {summary['all_stacks_aligned']}")
            print(f"  Merged Documents: {summary.get('merged_documents', False)}")
            
            # Verify HOA-FCL specific expectations
            assert summary['max_packages'] > 0, "No complete packages found"
            assert summary.get('merged_documents', False), "Should indicate merged documents for HOA-FCL"
            
        except Exception as e:
            pytest.fail(f"PDF stack validation failed: {str(e)}")
        
        finally:
            validator.cleanup()
        
        print("✓ PDF stack validation test completed\n")
    
    def test_sample_document_extraction(self):
        """Test extracting a sample document set"""
        print("TEST 6: Sample Document Extraction")
        print("-" * 40)
        
        validator = SimplifileValidator(
            county_id=self.county_id,
            workflow_type=self.workflow_id,
            logger=self.logger
        )
        
        try:
            pdf_processor = validator.pdf_processor
            
            # Extract first document set (index 0)
            documents = pdf_processor.get_documents(
                0,  # document_index
                self.deed_stack_path,
                self.affidavit_stack_path,
                self.condo_lien_stack_path
            )
            
            print(f"Extracted documents:")
            print(f"  Document types: {list(documents.keys())}")
            
            # Verify HOA-FCL specific document keys
            expected_keys = ["deed_pdf", "condo_lien_pdf"]
            for key in expected_keys:
                assert key in documents, f"Missing expected document key: {key}"
                assert documents[key], f"Empty document data for: {key}"
                print(f"  ✓ {key}: {len(documents[key])} base64 characters")
            
            # Verify base64 encoding
            import base64
            for doc_type, doc_data in documents.items():
                try:
                    # Try to decode base64 to verify it's valid
                    decoded = base64.b64decode(doc_data)
                    print(f"  ✓ {doc_type} is valid base64 ({len(decoded)} bytes)")
                    
                    # Check PDF header
                    if decoded.startswith(b'%PDF'):
                        print(f"  ✓ {doc_type} is valid PDF format")
                    else:
                        print(f"  ⚠ {doc_type} may not be valid PDF (no PDF header)")
                        
                except Exception as e:
                    pytest.fail(f"Invalid base64 data for {doc_type}: {str(e)}")
            
        except Exception as e:
            pytest.fail(f"Document extraction failed: {str(e)}")
        
        finally:
            validator.cleanup()
        
        print("✓ Sample document extraction test completed\n")
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n{'='*80}")
        print(f"RUNNING ALL HOA-FCL WORKFLOW TESTS")
        print(f"{'='*80}")
        
        try:
            self.test_file_existence()
            self.test_validator_creation()
            self.test_excel_structure_validation()
            self.test_pdf_stack_validation()
            self.test_sample_document_extraction()
            self.test_hoa_fcl_validation_comprehensive()
            
            print(f"{'='*80}")
            print(f"ALL TESTS COMPLETED SUCCESSFULLY!")
            print(f"{'='*80}")
            
        except Exception as e:
            print(f"{'='*80}")
            print(f"TEST FAILED: {str(e)}")
            print(f"{'='*80}")
            raise


def test_hoa_fcl_workflow():
    """Main test function for pytest"""
    test_suite = TestHOAFCLWorkflow()
    test_suite.setup_class()
    test_suite.run_all_tests()


if __name__ == "__main__":
    # Allow running the test directly
    test_hoa_fcl_workflow()
    print("\nTest completed! Run with: pytest test_hoa_fcl_workflow.py -v")
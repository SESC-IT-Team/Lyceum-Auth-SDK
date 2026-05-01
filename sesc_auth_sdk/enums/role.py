from enum import Enum


class RoleType(str, Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"
    parent = "parent"

    staff_academic_department_worker = "staff:academic_department:worker"
    staff_academic_department_chief = "staff:academic_department:chief"

    staff_olympiad_support_department_worker = "staff:olympiad_support_department:worker"
    staff_olympiad_support_department_chief = "staff:olympiad_support_department:chief"

    staff_medical_station_worker = "staff:medical_station:worker"
    staff_medical_station_chief = "staff:medical_station:chief"

    staff_educational_department_worker = "staff:educational_department:worker"
    staff_educational_department_chief = "staff:educational_department:chief"

    staff_library_worker = "staff:library:worker"
    staff_library_chief = "staff:library:chief"

    staff_it_department_worker = "staff:it_department:worker"
    staff_it_department_chief = "staff:it_department:chief"

    staff_laboratory_of_tech_teaching_aids_worker = "staff:laboratory_of_tech_teaching_aids:worker"
    staff_laboratory_of_tech_teaching_aids_chief = "staff:laboratory_of_tech_teaching_aids:chief"

    staff_competitive_selection_department_worker = "staff:competitive_selection_department:worker"
    staff_competitive_selection_department_chief = "staff:competitive_selection_department:chief"

    staff_additional_education_department_worker = "staff:additional_education_department:worker"
    staff_additional_education_department_chief = "staff:additional_education_department:chief"


class Roles:
    admin = RoleType.admin
    teacher = RoleType.teacher
    student = RoleType.student
    parent = RoleType.parent

    class Staff:
        class AcademicDepartment:
            worker = RoleType.staff_academic_department_worker
            chief = RoleType.staff_academic_department_chief

        class OlympiadSupportDepartment:
            worker = RoleType.staff_olympiad_support_department_worker
            chief = RoleType.staff_olympiad_support_department_chief

        class MedicalStation:
            worker = RoleType.staff_medical_station_worker
            chief = RoleType.staff_medical_station_chief

        class EducationalDepartment:
            worker = RoleType.staff_educational_department_worker
            chief = RoleType.staff_educational_department_chief

        class Library:
            worker = RoleType.staff_library_worker
            chief = RoleType.staff_library_chief

        class ITDepartment:
            worker = RoleType.staff_it_department_worker
            chief = RoleType.staff_it_department_chief

        class LaboratoryOfTechTeachingAids:
            worker = RoleType.staff_laboratory_of_tech_teaching_aids_worker
            chief = RoleType.staff_laboratory_of_tech_teaching_aids_chief

        class CompetitiveSelectionDepartment:
            worker = RoleType.staff_competitive_selection_department_worker
            chief = RoleType.staff_competitive_selection_department_chief

        class AdditionalEducationDepartment:
            worker = RoleType.staff_additional_education_department_worker
            chief = RoleType.staff_additional_education_department_chief

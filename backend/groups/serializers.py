from rest_framework import serializers
from .models import Group, BeneficiaryAssignment
from beneficiaries.models import Beneficiary
from volunteers.models import Volunteer


class BeneficiaryAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for volunteer-beneficiary assignments."""
    volunteer_name = serializers.CharField(source='volunteer.full_name', read_only=True)
    beneficiary_name = serializers.CharField(source='beneficiary.full_name', read_only=True)

    class Meta:
        model = BeneficiaryAssignment
        fields = ['id', 'beneficiary', 'volunteer', 'volunteer_name', 'beneficiary_name', 'is_main', 'additional_info', 'created_at']
        read_only_fields = ['created_at']


class BeneficiaryInGroupSerializer(serializers.Serializer):
    """Nested serializer for beneficiaries within a group detail view."""
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    phone = serializers.CharField(allow_null=True)
    address = serializers.CharField()
    status = serializers.CharField()
    volunteers = serializers.SerializerMethodField()

    def get_volunteers(self, obj):
        assignments = obj.volunteer_assignments.select_related('volunteer').all()
        return [
            {
                'id': a.volunteer.id,
                'full_name': a.volunteer.full_name,
                'assignment_id': a.id,
                'is_main': a.is_main,
                'additional_info': a.additional_info,
            }
            for a in assignments
        ]


class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for Group model with advanced mass assignment support.
    Accepts 'assignments' data to link beneficiaries and volunteers in one go.
    """
    leader_name = serializers.CharField(source='leader.full_name', read_only=True, default=None)
    beneficiary_count = serializers.IntegerField(read_only=True)
    volunteer_count = serializers.IntegerField(read_only=True)
    beneficiaries = BeneficiaryInGroupSerializer(many=True, read_only=True)
    
    # Advanced field for mass assignment: [ { beneficiary: id, volunteers: [ids] } ]
    assignments = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Group
        fields = [
            'id', 'name', 'leader', 'leader_name', 
            'beneficiary_count', 'volunteer_count', 
            'beneficiaries', 'assignments'
        ]
        read_only_fields = ['beneficiary_count', 'volunteer_count', 'beneficiaries']

    def validate_assignments(self, value):
        if not value:
            return value
            
        new_beneficiary_ids = [item['beneficiary'] for item in value]
        
        # Check for duplicate beneficiaries in the same request
        if len(new_beneficiary_ids) != len(set(new_beneficiary_ids)):
            raise serializers.ValidationError("Zduplikowani podopieczni w przypisaniach.")

        # Ensure none of these beneficiaries belong to another group
        conflicting = Beneficiary.objects.filter(id__in=new_beneficiary_ids).exclude(group__isnull=True)
        if self.instance:
            conflicting = conflicting.exclude(group=self.instance)
            
        if conflicting.exists():
            names = ", ".join([b.full_name for b in conflicting])
            raise serializers.ValidationError(f"Następujący podopieczni są już przypisani do innej grupy: {names}")
            
        return value

    def save(self, **kwargs):
        assignments_data = self.validated_data.pop('assignments', None)
        instance = super().save(**kwargs)
        
        if assignments_data is not None:
            # 1. Collect all beneficiaries in this group according to the new data
            new_beneficiary_ids = [a['beneficiary'] for a in assignments_data]
            
            # 2. Clear group FK for beneficiaries no longer in this group
            Beneficiary.objects.filter(group=instance).exclude(id__in=new_beneficiary_ids).update(group=None)
            
            # 3. Update group FK for all beneficiaries in the list
            Beneficiary.objects.filter(id__in=new_beneficiary_ids).update(group=instance)
            
            # 4. Handle per-beneficiary volunteer assignments
            all_assigned_volunteers = set()
            for item in assignments_data:
                beneficiary_id = item['beneficiary']
                volunteer_ids = item.get('volunteers', [])
                main_volunteer_id = item.get('main_volunteer', None)
                
                beneficiary = Beneficiary.objects.get(id=beneficiary_id)
                
                # Clear existing assignments for this specific beneficiary
                BeneficiaryAssignment.objects.filter(beneficiary=beneficiary).delete()
                
                # Create new assignments
                # volunteers may be plain IDs or {id, additional_info} objects
                for v_entry in volunteer_ids:
                    if isinstance(v_entry, dict):
                        v_id = v_entry['id']
                        additional_info = v_entry.get('additional_info', '')
                    else:
                        v_id = v_entry
                        additional_info = ''
                    volunteer = Volunteer.objects.get(id=v_id)
                    is_main = (v_id == main_volunteer_id)
                    BeneficiaryAssignment.objects.create(
                        beneficiary=beneficiary,
                        volunteer=volunteer,
                        is_main=is_main,
                        additional_info=additional_info,
                    )
                    all_assigned_volunteers.add(v_id)
            
            # 5. Sync the group's volunteer pool with all assigned volunteers
            instance.volunteers.set(list(all_assigned_volunteers))
                    
        return instance

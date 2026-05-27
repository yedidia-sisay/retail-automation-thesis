from __future__ import annotations

from django.contrib.auth.models import User
from rest_framework import serializers


class UserProfileSerializer(serializers.ModelSerializer):
	groups = serializers.SerializerMethodField()

	class Meta:
		model = User
		fields = [
			"id",
			"username",
			"first_name",
			"last_name",
			"email",
			"groups",
			"is_staff",
			"is_superuser",
		]

	def get_groups(self, obj) -> list[str]:
		return list(obj.groups.values_list("name", flat=True))

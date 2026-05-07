from __future__ import annotations

from rest_framework import serializers

from apps.audit.models import ReceiptEvaluation


class ReceiptEvaluationSerializer(serializers.ModelSerializer):
	class Meta:
		model = ReceiptEvaluation
		fields = [
			"id",
			"receipt",
			"evaluated_by",
			"is_correct",
			"product_names_correct",
			"quantities_correct",
			"prices_correct",
			"subtotals_correct",
			"total_correct",
			"notes",
			"created_at",
			"updated_at",
		]
		read_only_fields = ["id", "evaluated_by", "created_at", "updated_at"]

	def create(self, validated_data):
		request = self.context.get("request")
		user = getattr(request, "user", None)
		if getattr(user, "is_authenticated", False):
			validated_data["evaluated_by"] = user
		return super().create(validated_data)

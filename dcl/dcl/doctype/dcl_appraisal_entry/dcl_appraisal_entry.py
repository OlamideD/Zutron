# -*- coding: utf-8 -*-
# Copyright (c) 2019, John Vincent Fiel and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


class DCLAppraisalEntry(Document):
    def autoname(self):
        self.name = self.employee_name + '/' +str(self.date)
    def validate(self):
        total = 0.0
        scores = 0.0
        for k in self.kpi:
            total += 5.0
            scores += k.average_rating

        if scores:
            self.remark_score = (scores / total) * 100.0
            if self.remark_score < 40.0:
                self.remark = "Unsatisfactory"
            elif self.remark_score >= 50.0 and self.remark_score < 65.0:
                self.remark = "Needs Improvement"
            elif self.remark_score >= 65.0 and self.remark_score < 75.0:
                self.remark = "Meets Job requirements"
            elif self.remark_score >= 75.0 and self.remark_score <= 80.0:
                self.remark = "Exceeds Job requirements"
            elif self.remark_score > 80.0:
                self.remark = "Outstanding"

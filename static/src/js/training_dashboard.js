/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class TrainingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            waitingApproval: 0,
            totalCourses: 0,
            totalStudents: 0,
            totalTrainers: 0,
            totalEnrollments: 0,
            paidEnrollments: 0,
            totalRevenue: 0,
            latestEnrollments: [],
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    async loadDashboardData() {
        this.state.totalCourses = await this.orm.searchCount(
            "training.course",
            []
        );

        this.state.totalStudents = await this.orm.searchCount(
            "training.student",
            []
        );

        this.state.totalTrainers = await this.orm.searchCount(
            "training.trainer",
            []
        );

        this.state.totalEnrollments = await this.orm.searchCount(
            "training.enrollment",
            []
        );

        this.state.paidEnrollments = await this.orm.searchCount(
            "training.enrollment",
            [["state", "=", "paid"]]
        );
        this.state.waitingApproval = await this.orm.searchCount(
            "training.enrollment",
            [["state", "=", "waiting_approval"]]
        );

        const paidRecords = await this.orm.searchRead(
            "training.enrollment",
            [["state", "=", "paid"]],
            ["paid_amount"]
        );

        this.state.totalRevenue = paidRecords.reduce((total, rec) => {
            return total + rec.paid_amount;
        }, 0);

        this.state.latestEnrollments = await this.orm.searchRead(
            "training.enrollment",
            [],
            [
                "student_id",
                "course_id",
                "paid_amount",
                "due_amount",
                "state",
            ],
            {
                limit: 5,
                order: "id desc",
            }
        );
    }
    openWaitingApproval() {
    this.action.doAction({
        type: "ir.actions.act_window",
        name: "Waiting Approval",
        res_model: "training.enrollment",
        domain: [["state", "=", "waiting_approval"]],
        views: [[false, "list"], [false, "form"]],
        target: "current",
    });
}

    openCourses() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Courses",
            res_model: "training.course",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openStudents() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Students",
            res_model: "training.student",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openTrainers() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Trainers",
            res_model: "training.trainer",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openEnrollments() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Enrollments",
            res_model: "training.enrollment",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openPaidEnrollments() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Paid Enrollments",
            res_model: "training.enrollment",
            domain: [["state", "=", "paid"]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    async refreshDashboard() {
        await this.loadDashboardData();
    }
}

TrainingDashboard.template = "training_academy.TrainingDashboard";

registry.category("actions").add("training_dashboard", TrainingDashboard);
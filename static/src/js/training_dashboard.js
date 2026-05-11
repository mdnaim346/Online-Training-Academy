/** @odoo-module **/

import {
    Component,
    onWillStart,
    onMounted,
    useRef,
    useState,
} from "@odoo/owl";

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class TrainingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.revenueChartRef = useRef("revenueChart");
        this.statusChartRef = useRef("statusChart");

        this.revenueChart = null;
        this.statusChart = null;

        this.state = useState({
            totalCourses: 0,
            totalStudents: 0,
            totalTrainers: 0,
            totalEnrollments: 0,

            draftEnrollments: 0,
            waitingApproval: 0,
            confirmedEnrollments: 0,
            paidEnrollments: 0,
            cancelledEnrollments: 0,

            totalRevenue: 0,
            totalDue: 0,

            latestEnrollments: [],
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });

        onMounted(() => {
            this.renderCharts();
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

        this.state.draftEnrollments = await this.orm.searchCount(
            "training.enrollment",
            [["state", "=", "draft"]]
        );

        this.state.waitingApproval = await this.orm.searchCount(
            "training.enrollment",
            [["state", "=", "waiting_approval"]]
        );

        this.state.confirmedEnrollments = await this.orm.searchCount(
            "training.enrollment",
            [["state", "=", "confirmed"]]
        );

        this.state.paidEnrollments = await this.orm.searchCount(
            "training.enrollment",
            [["state", "=", "paid"]]
        );

        this.state.cancelledEnrollments = await this.orm.searchCount(
            "training.enrollment",
            [["state", "=", "cancelled"]]
        );

        const enrollments = await this.orm.searchRead(
            "training.enrollment",
            [],
            ["paid_amount", "due_amount"]
        );

        this.state.totalRevenue = enrollments.reduce((total, rec) => {
            return total + (rec.paid_amount || 0);
        }, 0);

        this.state.totalDue = enrollments.reduce((total, rec) => {
            return total + (rec.due_amount || 0);
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

    renderCharts() {
        if (!this.revenueChartRef.el || !this.statusChartRef.el) {
            return;
        }

        if (this.revenueChart) {
            this.revenueChart.destroy();
        }

        if (this.statusChart) {
            this.statusChart.destroy();
        }

        this.revenueChart = new Chart(this.revenueChartRef.el, {
            type: "bar",
            data: {
                labels: ["Revenue", "Due"],
                datasets: [
                    {
                        label: "Amount",
                        data: [
                            this.state.totalRevenue,
                            this.state.totalDue,
                        ],
                    },
                ],
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: true,
                    },
                },
            },
        });

        this.statusChart = new Chart(this.statusChartRef.el, {
            type: "doughnut",
            data: {
                labels: [
                    "Draft",
                    "Waiting Approval",
                    "Confirmed",
                    "Paid",
                    "Cancelled",
                ],
                datasets: [
                    {
                        label: "Enrollments",
                        data: [
                            this.state.draftEnrollments,
                            this.state.waitingApproval,
                            this.state.confirmedEnrollments,
                            this.state.paidEnrollments,
                            this.state.cancelledEnrollments,
                        ],
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                    },
                },
            },
        });
    }

    async refreshDashboard() {
        await this.loadDashboardData();
        this.renderCharts();
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

    openDuePayments() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Due Payments",
            res_model: "training.enrollment",
            domain: [["due_amount", ">", 0]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

TrainingDashboard.template = "training_academy.TrainingDashboard";

registry.category("actions").add("training_dashboard", TrainingDashboard);

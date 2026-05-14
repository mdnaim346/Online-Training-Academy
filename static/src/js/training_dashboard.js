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
        this.user = useService("user");

        this.revenueChartRef = useRef("revenueChart");
        this.statusChartRef = useRef("statusChart");

        this.revenueChart = null;
        this.statusChart = null;

        this.state = useState({
            totalCourses: 0,
            totalStudents: 0,
            totalTrainers: 0,
            totalEnrollments: 0,
            attendanceSessions: 0,
            todayActivities: 0,
            isManager: false,
            isPortal: false,

            draftEnrollments: 0,
            waitingApproval: 0,
            confirmedEnrollments: 0,
            paidEnrollments: 0,
            cancelledEnrollments: 0,

            totalRevenue: 0,
            totalDue: 0,
            pendingPayments: 0,
            certificatesIssued: 0,
            attendanceRiskStudents: 0,

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
        const data = await this.orm.call(
            "training.dashboard.service",
            "get_dashboard_data",
            [],
        );

        this.state.isManager = data.is_manager;
        this.state.isPortal = data.is_portal;
        this.state.totalCourses = data.total_courses || 0;
        this.state.totalStudents = data.total_students || 0;
        this.state.totalTrainers = data.total_trainers || 0;
        this.state.totalEnrollments = data.total_enrollments || 0;
        this.state.attendanceSessions = data.attendance_sessions || 0;
        this.state.todayActivities = data.today_activities || 0;
        this.state.draftEnrollments = data.draft_enrollments || 0;
        this.state.waitingApproval = data.waiting_approval || 0;
        this.state.confirmedEnrollments = data.confirmed_enrollments || 0;
        this.state.paidEnrollments = data.paid_enrollments || 0;
        this.state.cancelledEnrollments = data.cancelled_enrollments || 0;
        this.state.totalRevenue = data.total_revenue || 0;
        this.state.totalDue = data.total_due || 0;
        this.state.pendingPayments = data.pending_payments || 0;
        this.state.certificatesIssued = data.certificates_issued || 0;
        this.state.attendanceRiskStudents = data.attendance_risk_students || 0;
        this.state.latestEnrollments = data.latest_enrollments || [];
    }

    renderCharts() {
        if (!this.statusChartRef.el) {
            return;
        }

        if (this.revenueChart) {
            this.revenueChart.destroy();
        }

        if (this.statusChart) {
            this.statusChart.destroy();
        }

        if (this.state.isManager && this.revenueChartRef.el) {
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
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: true,
                        },
                    },
                },
            });
        }

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

    openAttendanceSessions() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Attendance Sessions",
            res_model: "training.attendance.session",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openTodayActivities() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Today's Activities",
            res_model: "mail.activity",
            domain: [["user_id", "=", this.user.userId]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openPendingPayments() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Pending Payments",
            res_model: "training.enrollment",
            domain: [["state", "=", "confirmed"], ["due_amount", ">", 0]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openCertificates() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Certificates Issued",
            res_model: "training.enrollment",
            domain: [["certificate_number", "!=", false]],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openAttendanceRisk() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Attendance Risk Students",
            res_model: "training.enrollment",
            domain: [
                ["state", "in", ["confirmed", "paid"]],
                ["total_sessions", ">", 0],
                ["attendance_percentage", "<", 80],
            ],
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

TrainingDashboard.template = "training_academy.TrainingDashboard";

registry.category("actions").add("training_dashboard", TrainingDashboard);

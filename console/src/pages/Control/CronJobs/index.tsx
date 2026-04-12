import { useState } from "react";
import { Button, Card, Form, Modal, Table } from "@agentscope-ai/design";
import type { CronJobSpecOutput } from "../../../api/types";
import { useTranslation } from "react-i18next";
import {
  createColumns,
  JobDrawer,
  useCronJobs,
  DEFAULT_FORM_VALUES,
} from "./components";
import styles from "./index.module.less";

type CronJob = CronJobSpecOutput;

function CronJobsPage() {
  const { t } = useTranslation();
  const {
    jobs,
    loading,
    createJob,
    updateJob,
    deleteJob,
    toggleEnabled,
    executeNow,
  } = useCronJobs();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [editingJob, setEditingJob] = useState<CronJob | null>(null);
  const [form] = Form.useForm<CronJob>();

  const handleCreate = () => {
    setEditingJob(null);
    form.resetFields();
    form.setFieldsValue(DEFAULT_FORM_VALUES);
    setDrawerOpen(true);
  };

  const handleEdit = (job: CronJob) => {
    setEditingJob(job);

    const formValues = {
      ...job,
      request: {
        ...job.request,
        input: job.request?.input
          ? JSON.stringify(job.request.input, null, 2)
          : "",
      },
    };

    form.setFieldsValue(formValues as any);
    setDrawerOpen(true);
  };

  const handleDelete = (jobId: string) => {
    Modal.confirm({
      title: t("cronJobs.confirmDelete"),
      content: t("cronJobs.deleteConfirm"),
      okText: t("cronJobs.deleteText"),
      okType: "primary",
      cancelText: t("cronJobs.cancelText"),
      onOk: async () => {
        await deleteJob(jobId);
      },
    });
  };

  const handleToggleEnabled = async (job: CronJob) => {
    await toggleEnabled(job);
  };

  const handleExecuteNow = async (job: CronJob) => {
    Modal.confirm({
      title: "Execute Now",
      content: `Are you sure you want to execute "${job.name}" now?`,
      okText: "Execute",
      okType: "primary",
      cancelText: "Cancel",
      onOk: async () => {
        await executeNow(job.id);
      },
    });
  };

  const handleDrawerClose = () => {
    setDrawerOpen(false);
    setEditingJob(null);
  };

  const handleSubmit = async (values: CronJob) => {
    let processedValues = { ...values };

    if (values.request?.input && typeof values.request.input === "string") {
      try {
        processedValues = {
          ...values,
          request: {
            ...values.request,
            input: JSON.parse(values.request.input as any),
          },
        };
      } catch (error) {
        console.error("❌ Failed to parse request.input JSON:", error);
      }
    }

    let success = false;
    if (editingJob) {
      success = await updateJob(editingJob.id, processedValues);
    } else {
      success = await createJob(processedValues);
    }
    if (success) {
      setDrawerOpen(false);
    }
  };

  const columns = createColumns({
    onToggleEnabled: handleToggleEnabled,
    onExecuteNow: handleExecuteNow,
    onEdit: handleEdit,
    onDelete: handleDelete,
    t,
  });

  return (
    <div className={styles.cronJobsPage}>
      <div className={styles.header}>
        <div className={styles.headerInfo}>
          <h1 className={styles.title}>{t("cronJobs.title")}</h1>
          <p className={styles.description}>{t("cronJobs.description")}</p>
        </div>
        <Button type="primary" onClick={handleCreate}>
          + {t("cronJobs.createJob")}
        </Button>
      </div>

      <Card className={styles.tableCard} bodyStyle={{ padding: 0 }}>
        <Table
          columns={columns}
          dataSource={jobs}
          loading={loading}
          rowKey="id"
          scroll={{ x: 2840 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: false,
            showTotal: (total) => t("cronJobs.totalItems", { count: total }),
          }}
        />
      </Card>

      <JobDrawer
        open={drawerOpen}
        editingJob={editingJob}
        form={form}
        onClose={handleDrawerClose}
        onSubmit={handleSubmit}
      />
    </div>
  );
}

export default CronJobsPage;
